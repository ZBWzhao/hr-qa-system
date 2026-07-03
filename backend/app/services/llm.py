import os
import re
import json
import subprocess
import tempfile
from app.core.config import settings


def call_mimo_api(messages: list, max_tokens: int = 500, temperature: float = 0.3) -> str:
    """调用小米MiMo API"""
    req_data = {
        "model": settings.MIMO_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    tmp_dir = tempfile.gettempdir()
    req_file = os.path.join(tmp_dir, "mimo_req.json")
    resp_file = os.path.join(tmp_dir, "mimo_resp.json")

    with open(req_file, "w", encoding="utf-8") as f:
        json.dump(req_data, f, ensure_ascii=False)

    try:
        subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{settings.MIMO_BASE_URL}/chat/completions",
            "-H", f"Authorization: Bearer {settings.MIMO_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", f"@{req_file}",
            "-o", resp_file
        ], timeout=60)

        with open(resp_file, "rb") as f:
            raw = f.read()

        # 解析响应
        resp = json.loads(raw.decode("utf-8"))

        if "error" in resp:
            return f"AI服务错误: {resp['error'].get('message', '未知错误')}"

        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

        # 如果content为空，可能是reasoning模型，尝试提取reasoning_content
        if not content:
            content = resp.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")

        return content.strip() if content else ""
    except subprocess.TimeoutExpired:
        return "AI服务响应超时，请稍后重试"
    except Exception as e:
        return f"AI服务异常: {str(e)}"


def is_ai_service_error(text: str) -> bool:
    """判断 LLM 返回是否为服务异常占位文本"""
    if not text or not str(text).strip():
        return True
    error_prefixes = ("AI服务错误", "AI服务异常", "AI服务响应超时")
    return any(str(text).strip().startswith(p) for p in error_prefixes)


def generate_knowledge_answer(
    question: str,
    knowledge: str,
    history: str = "",
    source_label: str = "标准答案",
    context_hint: str = "",
) -> str:
    """基于 FAQ/规则/制度等结构化知识，生成面向用户的自然语言回答"""
    if len(knowledge) > 2500:
        knowledge = knowledge[:2500] + "..."

    system_prompt = """你是公司HR智能问答助手。请根据提供的标准答案或制度规则，针对用户的实际问题给出自然、直接的回复。

要求：
1. 必须严格基于提供的知识内容回答，不得编造未提及的信息
2. 直接回答用户问题，不要使用「我理解您的问题是」「根据标准答案库查询」等套话
3. 语言简洁友好，优先给出用户最需要的核心信息（如电话、天数、金额、流程步骤等）
4. 若知识内容与用户具体问题高度相关，可结合对话上下文做简短个性化说明
5. 控制在300字以内，可适度使用 Markdown 突出重点"""

    parts = [f"【知识来源：{source_label}】\n{knowledge}"]
    if context_hint:
        parts.append(f"【对话上下文】\n{context_hint}")
    if history:
        parts.append(history.strip())
    parts.append(f"【用户问题】\n{question.strip()}")
    parts.append("请直接回答用户问题。")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(parts)},
    ]

    return call_mimo_api(messages, max_tokens=600, temperature=0.3)


def generate_answer(question: str, context: str, history: str = "") -> str:
    """基于知识库内容生成回答"""

    # 限制context长度，节省token
    if len(context) > 2000:
        context = context[:2000] + "..."

    system_prompt = """你是公司HR制度智能问答助手。请根据提供的制度文档内容回答用户问题。

要求：
1. 基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关内容，明确告知"根据现有知识库，未找到相关信息，无法回答"
3. 回答要简洁，控制在200字以内
4. 使用简洁的格式，不要过度使用Markdown"""

    user_content = f"""【制度文档内容】
{context}

{history}

【用户问题】
{question}

请基于上述文档内容回答用户问题。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    return call_mimo_api(messages, max_tokens=500, temperature=0.3)


def generate_clarification(question: str, possible_intents: list) -> str:
    """生成澄清回复"""

    intents_text = "\n".join([f"{i+1}. {intent}" for i, intent in enumerate(possible_intents)])

    system_prompt = """你是HR制度问答助手。用户的问题表述模糊或不清晰，请友好地提示用户描述更清晰。

要求：
1. 简洁友好，不超过100字
2. 给出2-3个可能的理解方向让用户选择
3. 提示用户补充关键信息"""

    user_content = f"""用户问题：{question}

可能的理解方向：
{intents_text}

请生成一个友好的澄清回复，让用户确认具体想问什么。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    return call_mimo_api(messages, max_tokens=300, temperature=0.5)


def _analyze_intent_rules(question: str) -> dict:
    """规则兜底：关键词意图分析"""
    intent_keywords = {
        "考勤": ["考勤", "打卡", "签到", "迟到", "早退", "加班", "工时"],
        "休假": ["年假", "病假", "事假", "婚假", "产假", "请假", "休假", "调休", "假期"],
        "薪酬": ["工资", "薪资", "奖金", "补贴", "社保", "公积金", "报销"],
        "绩效": ["绩效", "考核", "KPI", "晋升", "评级"],
        "福利": ["福利", "体检", "节日", "礼品", "团建"],
        "证明": ["证明", "在职", "收入", "开具"],
        "变更": ["变更", "修改", "更新", "信息"],
    }

    question_lower = question.lower()
    detected_intent = "其他"
    confidence = 0.5

    for intent, keywords in intent_keywords.items():
        for kw in keywords:
            if kw in question_lower:
                detected_intent = intent
                confidence = 0.8
                break
        if confidence > 0.5:
            break

    need_clarification = False
    clarification_reason = ""
    clarification_hint = ""

    if len(question) < 4:
        need_clarification = True
        clarification_reason = "问题太简短"
        clarification_hint = "请详细描述您想了解的内容"

    vague_references = ["这个", "那个", "它", "这个东西", "那个东西", "这个事情", "那个事情"]
    if any(ref in question for ref in vague_references):
        if len(question) < 12:
            need_clarification = True
            clarification_reason = "存在指代不明"
            clarification_hint = "请具体说明您指的是什么"

    return {
        "intent": detected_intent,
        "confidence": confidence,
        "need_clarification": need_clarification,
        "clarification_reason": clarification_reason,
        "clarification_hint": clarification_hint,
    }


def _parse_intent_json(text: str) -> dict | None:
    """从 LLM 返回中解析 JSON"""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "need_clarification" in data:
            return data
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict) and "need_clarification" in data:
                return data
        except json.JSONDecodeError:
            pass
    return None


def _parse_json_object(text: str) -> dict | None:
    """从 LLM 返回中解析 JSON 对象"""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return None


def extract_ticket_slots_with_ai(
    text: str,
    ticket_type: str,
    config: dict,
    filled: dict | None = None,
) -> dict | None:
    """使用 AI 从自然语言中提取/更新工单槽位"""
    text = text.strip()
    if not text:
        return None

    required = config.get("required_slots", [])
    labels = config.get("slot_labels", {})
    display = config.get("display_type", "工单")

    fields_lines = [f'- "{slot}": {labels.get(slot, slot)}' for slot in required]
    fields_desc = "\n".join(fields_lines)

    filled_desc = ""
    if filled:
        parts = []
        for slot in required:
            val = filled.get(slot)
            if val not in (None, ""):
                parts.append(f'- {labels.get(slot, slot)}: {val}')
        if parts:
            filled_desc = "【当前已填写】\n" + "\n".join(parts)

    type_hints = {
        "attendance_exception": (
            "考勤异常说明特别规则：\n"
            "1. 「2026年7月3日, 打卡缺失, 忘记打卡」→ exception_date=2026年7月3日, "
            "exception_type=打卡缺失, reason=忘记打卡\n"
            "2. exception_type 是异常类别（打卡缺失/忘记打卡/迟到/早退/补卡等），"
            "reason 是简短原因说明，二者不要混淆\n"
            "3. 用户修改字段时（如「异常原因改成忘记」「异常原因改成: 忘记」），"
            "只返回要改的字段，值中不要包含「改成」「改为」等动词\n"
        ),
        "certify": "证明开具：need_stamp 用 true/false。",
        "info_change": "信息变更：准确区分原信息与新信息。",
    }
    hint = type_hints.get(ticket_type, "")

    system_prompt = f"""你是 HR 工单信息提取助手。从用户输入中提取「{display}」工单的结构化字段。

{hint}
通用规则：
1. 只输出严格 JSON 对象，不要 markdown、不要解释
2. 键名必须使用英文字段名：{", ".join(required)}
3. 用户未提及或无法确定的字段不要出现在 JSON 中
4. 用户是在补充/修改已有信息时，只返回本次变更的字段
5. 值要简洁准确，不要把整句用户原文塞进单个字段"""

    user_parts = [f"【字段说明】\n{fields_desc}"]
    if filled_desc:
        user_parts.append(filled_desc)
    user_parts.append(f"【用户输入】\n{text}")
    user_parts.append("请输出 JSON：")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]

    raw = call_mimo_api(messages, max_tokens=350, temperature=0.05)
    if is_ai_service_error(raw):
        return None

    parsed = _parse_json_object(raw)
    if not parsed:
        return None

    result: dict = {}
    for slot in required:
        if slot not in parsed:
            continue
        val = parsed[slot]
        if val is None or val == "":
            continue
        if slot == "need_stamp":
            if isinstance(val, bool):
                result[slot] = val
            elif str(val).strip() in ("是", "要", "需要", "true", "True", "1"):
                result[slot] = True
            elif str(val).strip() in ("否", "不", "不要", "不用", "false", "False", "0"):
                result[slot] = False
        else:
            val_str = str(val).strip()
            val_str = re.sub(r"^(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*", "", val_str)
            val_str = re.sub(r"^[：:\s]+", "", val_str).strip()
            result[slot] = val_str

    return result if result else None


def analyze_intent(question: str, context_hint: str = "") -> dict:
    """分析用户问题意图（优先 AI，失败时规则兜底）"""
    llm_result = _analyze_intent_with_llm(question, context_hint)
    if llm_result:
        return llm_result
    return _analyze_intent_rules(question)


def _analyze_intent_with_llm(question: str, context_hint: str = "") -> dict | None:
    """使用 AI 判断问题是否清晰、是否需要澄清"""
    system_prompt = """你是公司HR智能问答助手的意图分析模块。判断用户问题是否足够清晰、能否直接检索回答。

返回严格 JSON（不要 markdown）：
{
  "intent": "考勤|休假|薪酬|绩效|福利|证明|变更|工单|其他",
  "need_clarification": false,
  "clarification_reason": "",
  "clarification_hint": "",
  "confidence": 0.9
}

规则：
1. 只有问题真正模糊、缺少关键信息、且无法从上下文推断时才 need_clarification=true
2. 工单办理中的追问（如「要等几天」「需要材料吗」「能不能加急」「会通知我吗」）是清晰问题，need_clarification=false，intent=工单
3. 带具体场景的问题（如「如果周五前来不及怎么办」在证明办理语境下）是清晰的，need_clarification=false
4. 纯指代且极短（如「这个呢？」）且无上下文时可 need_clarification=true
5. 不要因含有「怎么」「几天」「能不能」等词就一律要求澄清"""

    parts = [f"用户问题：{question.strip()}"]
    if context_hint:
        parts.append(f"对话上下文：\n{context_hint}")
    parts.append("请输出 JSON。")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(parts)},
    ]

    raw = call_mimo_api(messages, max_tokens=200, temperature=0.1)
    if is_ai_service_error(raw):
        return None

    parsed = _parse_intent_json(raw)
    if not parsed:
        return None

    return {
        "intent": parsed.get("intent", "其他"),
        "confidence": float(parsed.get("confidence", 0.8)),
        "need_clarification": bool(parsed.get("need_clarification", False)),
        "clarification_reason": parsed.get("clarification_reason", ""),
        "clarification_hint": parsed.get("clarification_hint", ""),
    }
