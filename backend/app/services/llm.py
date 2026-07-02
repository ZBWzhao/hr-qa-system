import os
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


def analyze_intent(question: str) -> dict:
    """分析用户问题意图"""
    import re

    # 简单的关键词意图分析，不调用API
    intent_keywords = {
        "考勤": ["考勤", "打卡", "签到", "迟到", "早退", "加班", "工时"],
        "休假": ["年假", "病假", "事假", "婚假", "产假", "请假", "休假", "调休", "假期"],
        "薪酬": ["工资", "薪资", "奖金", "补贴", "社保", "公积金", "报销"],
        "绩效": ["绩效", "考核", "KPI", "晋升", "评级"],
        "福利": ["福利", "体检", "节日", "礼品", "团建"],
        "证明": ["证明", "在职", "收入", "开具"],
        "变更": ["变更", "修改", "更新", "信息"]
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

    # 智能澄清判断
    need_clarification = False
    clarification_reason = ""
    clarification_hint = ""

    # 1. 问题太短（少于4个字）
    if len(question) < 4:
        need_clarification = True
        clarification_reason = "问题太简短"
        clarification_hint = "请详细描述您想了解的内容"

    # 2. 指代不明（使用了"这个"、"那个"、"它"等代词）
    vague_references = ["这个", "那个", "它", "这个东西", "那个东西", "这个事情", "那个事情"]
    if any(ref in question for ref in vague_references):
        need_clarification = True
        clarification_reason = "存在指代不明"
        clarification_hint = "请具体说明您指的是什么"

    # 3. 模糊请求（只有动词没有对象）
    vague_requests = ["怎么办", "怎么弄", "怎么做", "帮我", "告诉我", "解释一下", "说一下"]
    if any(req in question for req in vague_requests):
        # 检查是否有具体对象
        has_object = len(question) > 8 and any(kw in question for kw_list in intent_keywords.values() for kw in kw_list)
        if not has_object:
            need_clarification = True
            clarification_reason = "请求不够具体"
            clarification_hint = "请说明您想了解哪方面的内容"

    # 4. 疑问词开头但没有具体内容
    question_starters = ["怎么", "如何", "什么", "为什么", "多少", "几天", "能不能", "可不可以"]
    if any(question.startswith(starter) for starter in question_starters):
        if len(question) < 8:
            need_clarification = True
            clarification_reason = "问题不够完整"
            clarification_hint = "请补充更多细节，例如具体场景或对象"

    # 5. 检测到多个可能的意图
    matched_intents = []
    for intent, keywords in intent_keywords.items():
        if any(kw in question_lower for kw in keywords):
            matched_intents.append(intent)
    if len(matched_intents) > 2:
        need_clarification = True
        clarification_reason = "涉及多个主题"
        clarification_hint = f"您的问题可能涉及{'、'.join(matched_intents[:3])}等多个方面，请说明您最想了解的是哪个"

    return {
        "intent": detected_intent,
        "confidence": confidence,
        "need_clarification": need_clarification,
        "clarification_reason": clarification_reason,
        "clarification_hint": clarification_hint
    }
