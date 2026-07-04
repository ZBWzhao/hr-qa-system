from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.schemas.qa import FeedbackCreate, FeedbackOut, FeedbackHandle
from app.models.qa import QAFeedback, QARecord
from app.models.user import User
from app.services.llm import generate_feedback_handling_suggestion, sanitize_user_facing_text

router = APIRouter()


@router.post("")
def create_feedback(data: FeedbackCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(QARecord).filter(QARecord.id == data.record_id).first()
    if not record:
        return error("问答记录不存在")
    record.feedback = 1 if data.feedback_type == "useful" else 0
    feedback = QAFeedback(
        record_id=data.record_id,
        user_id=current_user.id,
        feedback_type=data.feedback_type,
        correction_text=data.correction_text,
        status="pending"
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return success(FeedbackOut.model_validate(feedback).model_dump())


@router.get("")
def list_feedback(status: Optional[str] = None, page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role in ("hr", "admin"):
        query = db.query(QAFeedback)
    else:
        query = db.query(QAFeedback).filter(QAFeedback.user_id == current_user.id)
    if status:
        query = query.filter(QAFeedback.status == status)
    total = query.count()
    items = query.order_by(QAFeedback.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for f in items:
        fb = FeedbackOut.model_validate(f).model_dump()
        record = db.query(QARecord).filter(QARecord.id == f.record_id).first()
        if record:
            fb["question"] = record.question
            fb["answer"] = record.answer[:200] if record.answer else ""
            fb["answer_type"] = record.answer_type
        else:
            fb["question"] = ""
            fb["answer"] = ""
            fb["answer_type"] = ""
        fb_user = db.query(User).filter(User.id == f.user_id).first()
        fb["user_name"] = fb_user.real_name if fb_user else "未知"
        result.append(fb)
    return paginated(result, total, page, page_size)


@router.get("/{feedback_id}/suggestion")
def get_feedback_suggestion(feedback_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """仅返回已缓存的 AI 建议，不自动调用 LLM"""
    feedback = db.query(QAFeedback).filter(QAFeedback.id == feedback_id).first()
    if not feedback:
        return error("反馈不存在")
    if feedback.ai_suggestion:
        return success({
            "suggestion": feedback.ai_suggestion,
            "cached": True,
            "generated_at": feedback.ai_suggestion_at.isoformat() if feedback.ai_suggestion_at else None,
        })
    return success({"suggestion": "", "cached": False})


@router.post("/{feedback_id}/suggestion")
def generate_feedback_suggestion(
    feedback_id: int,
    force: int = 0,
    current_user: User = Depends(require_roles("hr")),
    db: Session = Depends(get_db),
):
    """点击按钮后生成 AI 建议；force=1 时忽略缓存重新生成"""
    feedback = db.query(QAFeedback).filter(QAFeedback.id == feedback_id).first()
    if not feedback:
        return error("反馈不存在")

    if feedback.status != "pending" and not feedback.ai_suggestion:
        return error("已处理的反馈无需生成 AI 建议")

    if feedback.ai_suggestion and not force:
        return success({
            "suggestion": feedback.ai_suggestion,
            "cached": True,
            "generated_at": feedback.ai_suggestion_at.isoformat() if feedback.ai_suggestion_at else None,
        })

    record = db.query(QARecord).filter(QARecord.id == feedback.record_id).first()
    question = record.question if record else ""
    answer = record.answer if record else ""
    suggestion = sanitize_user_facing_text(
        generate_feedback_handling_suggestion(question, answer, feedback.correction_text or ""),
        fallback="建议：核对问答是否答非所问或信息过时，必要时更新制度文档或发布通知公告。",
    )
    feedback.ai_suggestion = suggestion
    feedback.ai_suggestion_at = datetime.now()
    db.commit()
    return success({
        "suggestion": suggestion,
        "cached": False,
        "regenerated": bool(force),
        "generated_at": feedback.ai_suggestion_at.isoformat(),
    })


@router.put("/{feedback_id}/handle")
def handle_feedback(feedback_id: int, data: FeedbackHandle, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    feedback = db.query(QAFeedback).filter(QAFeedback.id == feedback_id).first()
    if not feedback:
        return error("反馈不存在")
    feedback.status = data.status
    feedback.handle_note = data.handle_note
    feedback.handler_id = current_user.id
    feedback.handled_at = datetime.now()
    db.commit()
    db.refresh(feedback)
    fb = FeedbackOut.model_validate(feedback).model_dump()
    record = db.query(QARecord).filter(QARecord.id == feedback.record_id).first()
    if record:
        fb["question"] = record.question
        fb["answer"] = record.answer[:200] if record.answer else ""
        fb["answer_type"] = record.answer_type
    fb_user = db.query(User).filter(User.id == feedback.user_id).first()
    fb["user_name"] = fb_user.real_name if fb_user else "未知"
    return success(fb)


@router.get("/stats")
def feedback_stats(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    total = db.query(QAFeedback).count()
    handled = db.query(QAFeedback).filter(QAFeedback.status != "pending").count()
    return success({"total": total, "handled": handled, "pending": total - handled, "handle_rate": round(handled / total * 100, 1) if total > 0 else 0})
