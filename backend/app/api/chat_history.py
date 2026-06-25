from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success, error, paginated
from app.schemas.qa import QARecordOut
from app.models.qa import QARecord
from app.models.user import User

router = APIRouter()


@router.get("")
def list_history(keyword: Optional[str] = None, is_favorite: Optional[int] = None, page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(QARecord).filter(QARecord.user_id == current_user.id)
    if keyword:
        query = query.filter(QARecord.question.contains(keyword) | QARecord.answer.contains(keyword))
    if is_favorite is not None:
        query = query.filter(QARecord.is_favorite == is_favorite)
    total = query.count()
    items = query.order_by(QARecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([QARecordOut.model_validate(r).model_dump() for r in items], total, page, page_size)


@router.put("/{record_id}/favorite")
def toggle_favorite(record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(QARecord).filter(QARecord.id == record_id, QARecord.user_id == current_user.id).first()
    if not record:
        return error("记录不存在")
    record.is_favorite = 0 if record.is_favorite else 1
    db.commit()
    return success({"is_favorite": record.is_favorite})


@router.delete("/{record_id}")
def delete_history(record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(QARecord).filter(QARecord.id == record_id, QARecord.user_id == current_user.id).first()
    if not record:
        return error("记录不存在")
    db.delete(record)
    db.commit()
    return success(None, "删除成功")
