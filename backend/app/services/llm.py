import os
import re
import json
import subprocess
import tempfile
from app.core.config import settings

_REASONING_MARKERS = (
    "首先，", "首先,", "我需要", "我需要基于", "用户的问题是", "用户提到",
    "从知识内容中", "根据指令", "指令要求", "让我", "我来", "知识来源有",
    "用户想了解", "检查这些信息", "从知识内容", "不得编造",
)

_FINAL_ANSWER_PATTERNS = (
    r"(?:因此|所以|综上所述|总结来说|直接回答)[：:，,\s]*(.+)",
    r"(?:核心信息[是为]|最终答案[是为])[：:，,\s]*(.+)",
)


def looks_like_internal_reasoning(text: str) -> bool:
    if not text or not str(text).strip():
        return True
    t = str(text).strip()
    head = t[:280]
    marker_hits = sum(1 for m in _REASONING_MARKERS if m in head)
    if marker_hits >= 2:
        return True
    if t.startswith("首先") and len(t) > 120:
        return True
    if "用户的问题" in head and "知识内容" in t[:500]:
        return True
    return False


def looks_truncated(text: str) -> bool:
    if not text or not str(text).strip():
        return True
    t = str(text).strip()
    if len(t) < 12:
        return True
    if t[-1] in "。！？.!?」》\"'":
        return False
    bad_endings = ("，", "、", "月", "日", "的", "是", "在", "为", "和", "与", "及", "到", "请")
    if any(t.endswith(x) for x in bad_endings):
        return True
    if re.search(r"根据.{0,20}(知识|文档|内容|信息)[，,]?$", t):
        return True
    return False


def extract_final_answer(text: str) -> str:
    if not text:
        return ""
    t = str(text).strip()
    for pattern in _FINAL_ANSWER_PATTERNS:
        m = re.search(pattern, t, re.DOTALL)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) >= 20 and not looks_like_internal_reasoning(candidate):
                return candidate

    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    for i, line in enumerate(lines):
        if any(line.startswith(m.rstrip("，,")) for m in _REASONING_MARKERS):
            continue
        if line.startswith("用户") and "问题" in line:
            continue
        candidate = "\n".join(lines[i:]).strip()
        if len(candidate) >= 20:
            return candidate
    return t


def sanitize_user_facing_text(text: str, fallback: str = "") -> str:
    if is_ai_service_error(text):
        return fallback
    if not text or not str(text).strip():
        return fallback

    cleaned = str(text).strip()
    if looks_like_internal_reasoning(cleaned):
        extracted = extract_final_answer(cleaned)
        if extracted and not looks_like_internal_reasoning(extracted):
            cleaned = extracted
        else:
            return fallback

    if looks_truncated(cleaned):
        extracted = extract_final_answer(cleaned)
        if extracted and not looks_truncated(extracted) and not looks_like_internal_reasoning(extracted):
            cleaned = extracted
        else:
            return fallback

    return cleaned


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
5. 控制在300字以内，可适度使用 Markdown 突出重点
6. 严禁输出思考过程、分析步骤或内心独白（如「首先」「我需要」「用户的问题是」），只输出给用户看的最终答案"""

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

    raw = call_mimo_api(messages, max_tokens=900, temperature=0.3)
    return sanitize_user_facing_text(raw, fallback="")


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
4. 使用简洁的格式，不要过度使用Markdown
5. 严禁输出思考过程或分析步骤，只输出最终答案"""

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

    raw = call_mimo_api(messages, max_tokens=800, temperature=0.3)
    return sanitize_user_facing_text(raw, fallback="")


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


def generate_feedback_handling_suggestion(
    question: str,
    answer: str,
    correction_text: str = "",
) -> str:
    """为 HR 生成反馈/纠错处理建议"""
    prompt = f"""你是 HR 知识库管理员助手。员工对以下问答给出了「无用」反馈或纠错，请给出简洁的处理建议（3-5条要点）。

原问题：{question}
系统回答：{answer[:800]}
员工纠错/说明：{correction_text or '（未填写，仅标记无用）'}

请输出：
1. 问题根因（答非所问/信息过时/知识库缺失等）
2. 建议动作（更新制度文档/补充公告/修订标准答案/忽略等）
3. 如需补充知识，给出建议录入的要点（1-2句）

控制在150字以内，使用条目列表。"""

    messages = [
        {"role": "system", "content": "你是 HR Copilot 知识运营助手，输出简洁可执行的处理建议。"},
        {"role": "user", "content": prompt},
    ]
    result = call_mimo_api(messages, max_tokens=300, temperature=0.2)
    if is_ai_service_error(result):
        if correction_text:
            return f"建议：根据员工纠错「{correction_text[:100]}」核对制度文档或发布公告更新；确认后可标记已处理。"
        return "建议：核对问答是否答非所问或信息过时，必要时更新制度文档或发布通知公告。"
    return sanitize_user_facing_text(result.strip(), fallback=result.strip())


def sanitize_interpretation_text(text: str, fallback: str = "") -> str:
    """解读模式专用：比通用 sanitize 更宽松，避免误杀可用回答"""
    if is_ai_service_error(text):
        return fallback
    if not text or not str(text).strip():
        return fallback

    cleaned = str(text).strip()
    if looks_like_internal_reasoning(cleaned):
        extracted = extract_final_answer(cleaned)
        if extracted and not looks_like_internal_reasoning(extracted):
            cleaned = extracted
        elif len(cleaned) >= 80 and "**" in cleaned:
            pass
        else:
            return fallback

    if looks_truncated(cleaned) and len(cleaned) < 80:
        extracted = extract_final_answer(cleaned)
        if extracted and len(extracted) >= 40:
            cleaned = extracted
        else:
            return fallback

    return cleaned


def _interpretation_legal_score(answer: str) -> int:
    """条文式表述越多，分数越高（越像原文复述）"""
    if not answer:
        return 999
    t = str(answer)
    score = len(re.findall(r"第[一二三四五六七八九十百\d]+条", t)) * 3
    score += len(re.findall(r"第[一二三四五六七八九十百\d]+章", t)) * 5
    return score


def build_rule_based_interpretation(title: str, content: str) -> str:
    """LLM 不可用或持续复述原文时，本地提炼要点（非逐条抄原文）"""
    if not content or not str(content).strip():
        return ""

    bullets: list[str] = []
    for raw_line in str(content).splitlines():
        line = raw_line.strip()
        if not line or re.match(r"^第[一二三四五六七八九十百\d]+章", line):
            continue
        m = re.match(r"^第[一二三四五六七八九十百\d]+条\s*(.+)", line)
        if m:
            line = m.group(1).strip()
        line = re.sub(r"^\d+\.\s*", "", line)
        if len(line) >= 4 and not re.match(r"^第[一二三四五六七八九十百\d]+", line):
            bullets.append(line)

    if not bullets:
        return ""

    seen: set[str] = set()
    unique: list[str] = []
    for b in bullets:
        if b not in seen:
            seen.add(b)
            unique.append(b)

    body = "\n".join(f"- {b}" for b in unique[:10])
    return (
        f"**《{title}》通俗要点**\n\n"
        f"简单说，这份制度核心内容可以概括为：\n\n"
        f"{body}\n\n"
        f"*如需某一条的具体含义，可以继续追问，例如「绩效申诉怎么提？」。*"
    )


def _extract_title_from_knowledge(knowledge: str) -> str:
    m = re.match(r"【([^】]+)】", knowledge or "")
    return m.group(1).strip() if m else "制度文档"


def _extract_content_from_knowledge(knowledge: str) -> str:
    if not knowledge:
        return ""
    return re.sub(r"^【[^】]+】\s*", "", knowledge.strip())


def _pick_best_interpretation(candidates: list[str]) -> str:
    usable = [
        c for c in candidates
        if c and not is_ai_service_error(c) and len(c.strip()) >= 40
    ]
    if not usable:
        return ""

    good = [c for c in usable if not looks_like_document_restated(c)]
    if good:
        return min(good, key=_interpretation_legal_score)

    return min(usable, key=_interpretation_legal_score)


def looks_like_document_restated(answer: str) -> bool:
    """判断回答是否仍在按条文/章节复述原文，而非通俗解读"""
    if not answer or not str(answer).strip():
        return True
    t = str(answer).strip()
    if len(t) < 40:
        return True
    article_hits = len(re.findall(r"第[一二三四五六七八九十百\d]+条", t))
    chapter_hits = len(re.findall(r"第[一二三四五六七八九十百\d]+章", t))
    if chapter_hits >= 1 and article_hits >= 2:
        return True
    if article_hits >= 4:
        return True
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    legal_line_ratio = sum(
        1 for ln in lines
        if re.match(r"^第[一二三四五六七八九十百\d]+[章节条]", ln)
        or re.match(r"^[一二三四五六七八九十]+、", ln)
    ) / max(len(lines), 1)
    if legal_line_ratio >= 0.35 and article_hits >= 2:
        return True
    return False


def generate_interpretation_answer(
    question: str,
    knowledge: str,
    user_profile: str = "",
    history: str = "",
) -> str:
    """制度条文通俗解读，可选结合员工个人信息说明权益"""
    if len(knowledge) > 2500:
        knowledge = knowledge[:2500] + "..."

    system_prompt = """你是公司 HR 助手。用户要的是「大白话解读」，不是把制度原文再念一遍。

【禁止】
- 禁止按「第一章 / 第二条 / 第X条」逐条抄写或换行复述原文
- 禁止只把原文列表重新排版
- 禁止官话套话（如「根据本制度规定」「综上所述」）

【必须】
- 用你自己的话概括制度要点，像给同事口头解释一样
- 使用「简单说」「也就是说」「对你意味着」等口语
- 按主题归纳（如考核周期、怎么评、等级含义、申诉方式），不要按章节顺序
- 若提供了员工个人信息，说明这些规定对该员工的具体影响
- 控制在 400 字以内，可用 Markdown 小标题（不要用「第X章」作标题）
- 只输出最终解读，禁止思考过程"""

    if user_profile:
        output_format = """请按以下结构输出（标题可微调，但不要出现「第X条」）：
**这份制度讲什么**
（1-2 句总述）

**你需要知道的关键点**
（3-5 条口语化要点，每条一句话）

**对你意味着什么**
（结合上述员工信息说明具体影响）"""
    else:
        output_format = """请按以下结构输出（标题可微调，但不要出现「第X条」）：
**这份制度讲什么**
（1-2 句总述）

**你需要知道的关键点**
（3-5 条口语化要点，每条一句话）

**实际工作中怎么用**
（从一般员工视角说明这套制度怎么影响日常）"""

    def _call(extra_user_hint: str = "", knowledge_text: str = knowledge) -> str:
        parts = [f"【制度内容（仅供理解，勿复述）】\n{knowledge_text}"]
        if user_profile:
            parts.append(f"【员工信息】\n{user_profile}")
        if history:
            parts.append(history.strip())
        parts.append(f"【用户问题】\n{question.strip()}")
        parts.append(output_format)
        if extra_user_hint:
            parts.append(extra_user_hint)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(parts)},
        ]
        raw = call_mimo_api(messages, max_tokens=1200, temperature=0.4)
        return sanitize_interpretation_text(raw, fallback="")

    candidates = [
        _call(),
        _call(
            "上次输出过于接近原文条文。请完全改写：不要出现「第X章/第X条」，只用口语概括要点。"
        ),
    ]

    # 文档过长时，用摘要片段再试一次，降低模型逐条抄写倾向
    plain_content = _extract_content_from_knowledge(knowledge)
    if len(plain_content) > 1200:
        short_knowledge = f"【{_extract_title_from_knowledge(knowledge)}】\n{plain_content[:1200]}..."
        candidates.append(_call(
            "请基于摘要片段用大白话概括，不要引用章节编号。",
            knowledge_text=short_knowledge,
        ))

    best = _pick_best_interpretation(candidates)
    if best and not looks_like_document_restated(best):
        return best

    if best and _interpretation_legal_score(best) <= 6:
        return best

    title = _extract_title_from_knowledge(knowledge)
    rule_based = build_rule_based_interpretation(title, plain_content)
    if rule_based:
        return rule_based

    return best or ""


def generate_gap_analysis_summary(questions: list[str]) -> str:
    """对全部未解决知识缺口生成汇总分析与分类建议"""
    if not questions:
        return "当前没有未解决的知识缺口。"

    q_text = "\n".join(f"- {q}" for q in questions[:40])
    if len(questions) > 40:
        q_text += f"\n… 共 {len(questions)} 条"

    prompt = f"""你是 HR 知识库运营助手。以下是员工提问但未命中知识库的问题列表：

{q_text}

请输出：
1. **总体概况**（2-3句）：这些问题反映了哪些知识盲区
2. **分类建议**（按主题分类，如考勤/休假/薪酬/福利/其他）：每类给出 1-2 条可执行的补充建议（如发布哪类公告、补充哪类制度文档）

控制在400字以内，使用 Markdown 标题与列表。只输出最终分析，禁止思考过程。"""

    messages = [
        {"role": "system", "content": "你是 HR Copilot 知识运营助手。"},
        {"role": "user", "content": prompt},
    ]
    raw = call_mimo_api(messages, max_tokens=700, temperature=0.25)
    cleaned = sanitize_user_facing_text(raw, fallback="")
    if cleaned:
        return cleaned
    return "建议：针对高频未命中问题，补充相应的制度文档或发布通知公告。"


def correct_user_question_typos(text: str) -> str:
    """根据 HR 场景意图静默修正错别字/同音字/拼音混输，仅返回修正后的原句"""
    if not text or not str(text).strip():
        return text

    system_prompt = """你是 HR 智能助手输入理解模块。根据用户想表达的 HR/考勤/公告/制度/工单/福利咨询意图，静默修正输入中的错别字、同音字、拼音或英文混输。

规则：
1. 只输出修正后的完整用户原句，不要解释、不要前缀、不要 markdown
2. 若输入已清晰无误，原样输出
3. 不要回答问题，不要扩写，不要改变用户意图
4. 常见场景示例：
   - 「发布一折公告」→「发布一条公告」
   - 「公告表体」→「公告标题」
   - 「7yue15日呢」→「7月15日呢」"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"用户输入：{str(text).strip()}\n\n请输出修正后的句子："},
    ]
    raw = call_mimo_api(messages, max_tokens=150, temperature=0.05)
    if is_ai_service_error(raw):
        return text
    cleaned = sanitize_user_facing_text(raw, fallback=text)
    return cleaned or text
