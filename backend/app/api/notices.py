from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeOut
from app.models.notice import Notice, NoticeRead
from app.models.user import User

router = APIRouter()


@router.get("")
def list_notices(page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Notice)
    now = datetime.now()
    query = query.filter((Notice.expire_at == None) | (Notice.expire_at > now))
    total = query.count()
    items = query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    read_ids = set(r.notice_id for r in db.query(NoticeRead).filter(NoticeRead.user_id == current_user.id).all())
    result = []
    for n in items:
        d = NoticeOut.model_validate(n).model_dump()
        d["is_read"] = n.id in read_ids
        result.append(d)
    return paginated(result, total, page, page_size)


@router.get("/unread-count")
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    read_ids = set(r.notice_id for r in db.query(NoticeRead).filter(NoticeRead.user_id == current_user.id).all())
    now = datetime.now()
    total = db.query(Notice).filter((Notice.expire_at == None) | (Notice.expire_at > now)).count()
    read_count = len(read_ids)
    return success({"unread": total - read_count})


@router.get("/{notice_id}")
def get_notice(notice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        return error("通知不存在")
    existing = db.query(NoticeRead).filter(NoticeRead.notice_id == notice_id, NoticeRead.user_id == current_user.id).first()
    if not existing:
        db.add(NoticeRead(notice_id=notice_id, user_id=current_user.id))
        db.commit()
    d = NoticeOut.model_validate(notice).model_dump()
    d["is_read"] = True
    return success(d)


@router.post("")
def create_notice(data: NoticeCreate, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    notice = Notice(title=data.title, content=data.content, notice_type=data.notice_type, is_pinned=data.is_pinned, publisher_id=current_user.id, expire_at=data.expire_at)
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return success(NoticeOut.model_validate(notice).model_dump())


@router.put("/{notice_id}")
def update_notice(notice_id: int, data: NoticeUpdate, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        return error("通知不存在")
    if data.title is not None:
        notice.title = data.title
    if data.content is not None:
        notice.content = data.content
    if data.notice_type is not None:
        notice.notice_type = data.notice_type
    if data.is_pinned is not None:
        notice.is_pinned = data.is_pinned
    if data.expire_at is not None:
        notice.expire_at = data.expire_at
    db.commit()
    db.refresh(notice)
    return success(NoticeOut.model_validate(notice).model_dump())


@router.delete("/{notice_id}")
def delete_notice(notice_id: int, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        return error("通知不存在")
    db.query(NoticeRead).filter(NoticeRead.notice_id == notice_id).delete()
    db.delete(notice)
    db.commit()
    return success(None, "删除成功")
