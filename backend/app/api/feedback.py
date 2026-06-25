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
    return paginated([FeedbackOut.model_validate(f).model_dump() for f in items], total, page, page_size)


@router.put("/{feedback_id}/handle")
def handle_feedback(feedback_id: int, data: FeedbackHandle, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    feedback = db.query(QAFeedback).filter(QAFeedback.id == feedback_id).first()
    if not feedback:
        return error("反馈不存在")
    feedback.status = data.status
    feedback.handle_note = data.handle_note
    feedback.handler_id = current_user.id
    feedback.handled_at = datetime.now()
    db.commit()
    db.refresh(feedback)
    return success(FeedbackOut.model_validate(feedback).model_dump())


@router.get("/stats")
def feedback_stats(current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    total = db.query(QAFeedback).count()
    handled = db.query(QAFeedback).filter(QAFeedback.status != "pending").count()
    return success({"total": total, "handled": handled, "pending": total - handled, "handle_rate": round(handled / total * 100, 1) if total > 0 else 0})
