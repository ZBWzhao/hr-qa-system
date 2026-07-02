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

    # 检查是否需要澄清（问题太短或太模糊）
    need_clarification = False
    clarification_reason = ""

    if len(question) < 4:
        need_clarification = True
        clarification_reason = "问题太短，请描述更详细"
    elif not any(kw in question_lower for kw_list in intent_keywords.values() for kw in kw_list):
        # 没有匹配到任何关键词，可能是模糊问题
        vague_patterns = ["怎么办", "怎么弄", "如何", "是什么", "多少", "几天"]
        if any(p in question_lower for p in vague_patterns):
            if len(question) < 10:
                need_clarification = True
                clarification_reason = "问题表述不够具体，请补充更多细节"

    return {
        "intent": detected_intent,
        "confidence": confidence,
        "need_clarification": need_clarification,
        "clarification_reason": clarification_reason
    }
