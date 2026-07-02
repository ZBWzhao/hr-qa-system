import re
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success, error
from app.schemas.qa import ChatRequest, ChatResponse
from app.models.qa import QARecord, FAQ, Rule, QAMiss
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.services.rag.vectorstore import search_similar
from app.services.llm import generate_answer, analyze_intent, generate_clarification
from app.services.text_splitter import extract_keywords

router = APIRouter()


def get_or_create_conversation_id(db: Session, user_id: int, conversation_id: str = None) -> str:
    if conversation_id:
        return conversation_id
    return str(uuid.uuid4())[:16]


def get_conversation_context(db: Session, user_id: int, conversation_id: str, limit: int = 3) -> str:
    """获取对话历史上下文"""
    if not conversation_id:
        return ""
    records = db.query(QARecord).filter(
        QARecord.user_id == user_id,
        QARecord.conversation_id == conversation_id
    ).order_by(QARecord.created_at.desc()).limit(limit).all()
    if not records:
        return ""
    context = "以下是之前的对话记录：\n"
    for r in reversed(records):
        # 限制历史记录长度
        q = r.question[:50] if r.question else ""
        a = r.answer[:100] if r.answer else ""
        context += f"问：{q}\n答：{a}\n\n"
    return context


def match_faq(db: Session, question: str):
    """关键词匹配FAQ，不调用API"""
    keywords = extract_keywords(question)
    faqs = db.query(FAQ).filter(FAQ.status == 1).all()

    # 通用词列表，匹配时权重降低
    common_words = {'如何', '怎么', '什么', '为什么', '请', '帮我', '告诉', '一下',
                    '一些', '这个', '那个', '可以', '能否', '是否', '有没有', '想',
                    '知道', '了解', '咨询', '询问', '问', '答', '回答', '问题'}

    best_match = None
    best_score = 0

    q_lower = question.lower()

    for faq in faqs:
        score = 0

        # 完全匹配问题（高权重）
        if faq.question and (faq.question.lower() in q_lower or q_lower in faq.question.lower()):
            score += 10

        # 关键词匹配
        for kw in keywords:
            if not kw:
                continue

            # 通用词权重降低
            is_common = kw in common_words
            weight = 1 if is_common else 3

            if faq.question and kw in faq.question:
                score += weight
            if faq.keywords and kw in faq.keywords:
                score += weight

        if score > best_score:
            best_score = score
            best_match = faq

    # 阈值设为3，避免误匹配
    # 但如果只匹配到通用词，需要更高阈值
    if best_match and best_score >= 3:
        # 检查是否只匹配到了通用词
        matched_keywords = []
        for kw in keywords:
            if kw and ((faq.question and kw in faq.question) or (faq.keywords and kw in faq.keywords)):
                matched_keywords.append(kw)

        # 如果所有匹配到的关键词都是通用词，需要更高分数
        all_common = all(kw in common_words for kw in matched_keywords if kw)
        if all_common and best_score < 6:
            return None

        best_match.view_count += 1
        return best_match
    return None


def match_rule(db: Session, question: str):
    """关键词匹配规则，不调用API"""
    keywords = extract_keywords(question)
    rules = db.query(Rule).filter(Rule.status == 1).order_by(Rule.priority.desc()).all()

    for rule in rules:
        if not rule.trigger_keywords:
            continue
        triggers = [t.strip() for t in rule.trigger_keywords.split(",") if t.strip()]

        # 直接匹配触发词
        for trigger in triggers:
            if trigger and trigger in question:
                return rule

        # 关键词匹配
        for kw in keywords:
            if not kw:
                continue
            for trigger in triggers:
                if trigger and (kw in trigger or trigger in kw):
                    return rule
    return None


def rag_search_and_generate(question: str, history: str = "") -> tuple:
    """RAG搜索 + AI生成回答"""

    # 先进行意图分析（使用关键词，不调用API）
    intent_result = analyze_intent(question)

    # 如果需要澄清，返回澄清请求
    if intent_result.get("need_clarification", False):
        clarification_reason = intent_result.get("clarification_reason", "")
        clarification_hint = intent_result.get("clarification_hint", "请补充更多细节")
        intent = intent_result.get("intent", "其他")

        # 生成友好的澄清提示
        clarification = f"🤔 我注意到您的问题可能需要补充一些信息。\n\n"
        clarification += f"**问题分析：** {clarification_reason}\n\n"
        clarification += f"**建议：** {clarification_hint}\n\n"

        # 根据意图给出具体的提示
        if intent == "考勤":
            clarification += "例如：您可以问「请假需要提前多久申请？」或「加班可以调休吗？」"
        elif intent == "休假":
            clarification += "例如：您可以问「年假有几天？」或「病假需要什么证明？」"
        elif intent == "薪酬":
            clarification += "例如：您可以问「工资是怎么构成的？」或「社保缴纳比例是多少？」"
        elif intent == "绩效":
            clarification += "例如：您可以问「绩效考核标准是什么？」或「绩效申诉怎么提交？」"
        else:
            clarification += "例如：您可以问「试用期多久？」或「报销流程是什么？」"

        return clarification, [], "need_clarification"

    # 进行向量搜索
    search_results = search_similar(question, top_k=5)

    # 如果没有搜索结果或置信度太低
    if not search_results or search_results[0]["score"] < 0.3:
        return None, [], "low_confidence"

    # 构建上下文，限制长度
    context_parts = []
    sources = []
    for r in search_results[:3]:  # 只取前3个结果
        content = r["content"][:300]  # 限制每个chunk长度
        context_parts.append(content)
        meta = r.get("metadata", {})
        sources.append({
            "doc_id": meta.get("doc_id"),
            "chunk": content[:100],
            "score": round(r["score"], 3)
        })

    context = "\n\n".join(context_parts)

    # 调用AI生成回答
    answer = generate_answer(question, context, history)

    # 检查AI回答是否表示未找到信息
    miss_keywords = ["未找到", "无法回答", "没有找到", "未查询到", "没有相关信息", "暂未找到"]
    is_miss = any(kw in answer for kw in miss_keywords)

    if is_miss:
        return answer, sources, "low_confidence"

    return answer, sources, "high_confidence"


@router.post("")
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv_id = get_or_create_conversation_id(db, current_user.id, data.conversation_id)
    context = get_conversation_context(db, current_user.id, conv_id)
    question = data.question.strip()

    if not question:
        return error("请输入问题")

    # 第一步：关键词匹配FAQ（不调用API，快速响应）
    faq = match_faq(db, question)
    if faq:
        # 构建更有逻辑性的回答
        answer = f"我理解您的问题是关于「{faq.question}」。\n\n"
        answer += f"根据标准答案库查询，找到以下相关信息：\n\n"
        answer += f"**问题：** {faq.question}\n\n"
        answer += f"**答案：** {faq.answer}"
        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=answer,
            answer_type="faq",
            source_docs=json.dumps([{"faq_id": faq.id, "question": faq.question}]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "faq",
            "source_docs": [{"faq_id": faq.id, "question": faq.question}],
            "record_id": record.id,
            "conversation_id": conv_id
        })

    # 第二步：关键词匹配规则（不调用API，快速响应）
    rule = match_rule(db, question)
    if rule:
        # 构建更有逻辑性的回答
        answer = f"我理解您的问题，根据公司相关规则查询：\n\n"
        answer += f"**规则名称：** {rule.name}\n\n"
        answer += f"**规定内容：**\n{rule.answer_template}"
        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=answer,
            answer_type="rule",
            source_docs=json.dumps([{"rule_id": rule.id, "name": rule.name}]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "rule",
            "source_docs": [{"rule_id": rule.id, "name": rule.name}],
            "record_id": record.id,
            "conversation_id": conv_id
        })

    # 第三步：RAG搜索 + AI生成（调用API）
    answer, sources, confidence = rag_search_and_generate(question, context)

    # 意图不清晰，需要用户澄清
    if confidence == "need_clarification":
        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=answer,
            answer_type="clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "clarification",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "need_clarification": True
        })

    # 置信度低，未找到相关信息
    if confidence == "low_confidence":
        miss = QAMiss(user_id=current_user.id, question=question)
        db.add(miss)

        clarification = f"抱歉，关于「{question}」，当前知识库暂未找到明确依据。\n\n建议您：\n1. 换个关键词重新提问\n2. 联系HR部门获取帮助\n3. 提交工单进行详细咨询"

        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=clarification,
            answer_type="miss",
            source_docs=json.dumps([]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": clarification,
            "answer_type": "miss",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "need_clarification": True
        })

    # 高置信度，AI生成了回答
    record = QARecord(
        user_id=current_user.id,
        question=question,
        answer=answer,
        answer_type="rag",
        source_docs=json.dumps(sources),
        conversation_id=conv_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": answer,
        "answer_type": "rag",
        "source_docs": sources,
        "record_id": record.id,
        "conversation_id": conv_id
    })


@router.post("/save-record")
def save_chat_record(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """保存前端拦截的对话记录"""
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    answer_type = data.get("answer_type", "system")
    conversation_id = data.get("conversation_id")

    if not question or not answer:
        return error("问题和回答不能为空")

    # 如果没有 conversation_id，创建一个新的
    if not conversation_id:
        conversation_id = str(uuid.uuid4())[:16]

    record = QARecord(
        user_id=current_user.id,
        question=question,
        answer=answer,
        answer_type=answer_type,
        source_docs=json.dumps([]),
        conversation_id=conversation_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success({
        "record_id": record.id,
        "conversation_id": conversation_id
    })


@router.post("/voice")
def voice_chat(current_user: User = Depends(get_current_user)):
    mock_text = "语音识别结果：请问公司的年假政策是什么？"
    return success({
        "recognized_text": mock_text,
        "answer": "【语音问答Mock】\n\n根据公司制度，年假按照工龄计算：\n- 工龄1-10年：5天\n- 工龄10-20年：10天\n- 工龄20年以上：15天\n\n温馨提示：年假需提前申请，请合理安排。",
        "answer_type": "mock"
    })


@router.post("/image")
def image_chat(current_user: User = Depends(get_current_user)):
    mock_text = "OCR识别结果：报销单据"
    return success({
        "ocr_text": mock_text,
        "answer": "【图片问答Mock】\n\n已识别图片内容为报销单据。报销流程如下：\n1. 填写报销申请表\n2. 附上发票原件\n3. 部门主管审批\n4. 财务审核\n5. 打款\n\n温馨提示：报销需在消费后30天内提交。",
        "answer_type": "mock"
    })


@router.get("/stats")
def get_chat_stats(current_user: User = Depends(get_current_user)):
    from app.services.rag.vectorstore import get_collection_stats
    stats = get_collection_stats()
    return success(stats)


@router.get("/category-stats")
def get_category_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取咨询类别分布统计"""
    from sqlalchemy import func
    from app.models.qa import QARecord

    # 统计各类别的问答数量
    # 基于 answer_type 分类
    stats = db.query(
        QARecord.answer_type,
        func.count(QARecord.id)
    ).group_by(QARecord.answer_type).all()

    # 转换为前端需要的格式
    category_map = {
        'faq': '标准答案',
        'rule': '规则匹配',
        'rag': '文档检索',
        'miss': '未命中',
        'clarification': '澄清追问',
        'ticket_form': '工单申请',
        'ticket_submitted': '工单已提交',
        'notice_form': '公告发布',
        'notice_confirm': '公告确认',
        'no_permission': '无权限'
    }

    result = []
    for answer_type, count in stats:
        category = category_map.get(answer_type, '其他')
        result.append({
            'name': category,
            'value': count,
            'type': answer_type
        })

    # 按数量排序
    result.sort(key=lambda x: x['value'], reverse=True)

    return success(result)
