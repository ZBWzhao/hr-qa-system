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
        context += f"问：{r.question}\n答：{r.answer[:200]}\n\n"
    return context


def match_faq(db: Session, question: str):
    keywords = extract_keywords(question)
    faqs = db.query(FAQ).filter(FAQ.status == 1).all()
    best_match = None
    best_score = 0
    for faq in faqs:
        score = 0
        q_lower = question.lower()
        if faq.question.lower() in q_lower or q_lower in faq.question.lower():
            score += 10
        for kw in keywords:
            if kw in faq.question:
                score += 3
            if faq.keywords and kw in faq.keywords:
                score += 2
        if score > best_score:
            best_score = score
            best_match = faq
    if best_match and best_score >= 3:
        best_match.view_count += 1
        return best_match
    return None


def match_rule(db: Session, question: str):
    keywords = extract_keywords(question)
    rules = db.query(Rule).filter(Rule.status == 1).order_by(Rule.priority.desc()).all()
    for rule in rules:
        triggers = [t.strip() for t in rule.trigger_keywords.split(",")]
        for trigger in triggers:
            if trigger in question:
                return rule
        for kw in keywords:
            for trigger in triggers:
                if kw in trigger or trigger in kw:
                    return rule
    return None


def rag_search_and_generate(question: str, history: str = "") -> tuple:
    # 先进行意图分析
    intent_result = analyze_intent(question)

    # 如果需要澄清，返回澄清请求
    if intent_result.get("need_clarification", False):
        clarification_reason = intent_result.get("clarification_reason", "")
        possible_intents = [
            f"{intent_result.get('intent', '其他')}相关问题",
            "其他HR制度问题"
        ]
        clarification = generate_clarification(question, possible_intents)
        return clarification, [], "need_clarification"

    search_results = search_similar(question, top_k=5)

    if not search_results or search_results[0]["score"] < 0.3:
        return None, [], "low_confidence"

    context = "\n\n".join([r["content"] for r in search_results])
    sources = []
    for r in search_results:
        meta = r.get("metadata", {})
        sources.append({
            "doc_id": meta.get("doc_id"),
            "chunk": r["content"][:200],
            "score": round(r["score"], 3)
        })

    answer = generate_answer(question, context, history)

    return answer, sources, "high_confidence"


@router.post("")
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv_id = get_or_create_conversation_id(db, current_user.id, data.conversation_id)
    context = get_conversation_context(db, current_user.id, conv_id)
    question = data.question

    faq = match_faq(db, question)
    if faq:
        answer = f"【FAQ回答】\n\n{faq.answer}"
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

    rule = match_rule(db, question)
    if rule:
        answer = rule.answer_template
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

    answer, sources, confidence = rag_search_and_generate(question, context)

    if confidence == "need_clarification":
        # 意图不清晰，需要用户澄清
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
