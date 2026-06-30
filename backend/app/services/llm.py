from openai import OpenAI
from app.core.config import settings

_client = None


def get_llm_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
    return _client


def generate_answer(question: str, context: str, history: str = "") -> str:
    client = get_llm_client()

    system_prompt = """你是公司HR制度智能问答助手。请根据提供的制度文档内容回答用户问题。

要求：
1. 基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关内容，明确告知用户
3. 回答要简洁、准确、易懂
4. 适当引用文档来源
5. 使用Markdown格式美化回答"""

    user_content = f"""【制度文档内容】
{context}

{history}

【用户问题】
{question}

请基于上述文档内容回答用户问题。"""

    response = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.3,
        max_tokens=1024
    )

    return response.choices[0].message.content


def generate_clarification(question: str, possible_intents: list[str]) -> str:
    client = get_llm_client()

    system_prompt = """你是HR制度问答助手。用户的问题不够清晰，请生成一个澄清回复。
要求简洁友好，给出2-3个可能的理解方向让用户选择。"""

    intents_text = "\n".join([f"{i+1}. {intent}" for i, intent in enumerate(possible_intents)])
    user_content = f"""用户问题：{question}

可能的理解方向：
{intents_text}

请生成一个友好的澄清回复，让用户确认具体想问什么。"""

    response = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.5,
        max_tokens=300
    )

    return response.choices[0].message.content


def analyze_intent(question: str) -> dict:
    client = get_llm_client()

    system_prompt = """分析用户问题的意图，返回JSON格式：
{
    "intent": "问题类型（考勤/休假/薪酬/报销/绩效/其他）",
    "confidence": 0.0-1.0,
    "need_clarification": true/false,
    "clarification_reason": "需要澄清的原因（如果不需要则为空）"
}"""

    response = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.1,
        max_tokens=200,
        response_format={"type": "json_object"}
    )

    import json
    return json.loads(response.choices[0].message.content)
