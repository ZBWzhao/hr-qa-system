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
def list_notices(
    page: int = 1,
    page_size: int = 20,
    filter_type: str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_
    query = db.query(Notice)
    now = datetime.now()
    query = query.filter((Notice.expire_at == None) | (Notice.expire_at > now))
    # 部门隔离：非管理员只能看到自己部门的公告或通用公告（department_id 为 None）
    if current_user.role != "admin" and current_user.department_id:
        query = query.filter(or_(Notice.department_id == current_user.department_id, Notice.department_id == None))

    read_ids = set(
        r.notice_id
        for r in db.query(NoticeRead).filter(NoticeRead.user_id == current_user.id).all()
    )

    if filter_type == "unread":
        if read_ids:
            query = query.filter(~Notice.id.in_(read_ids))
    elif filter_type == "pinned":
        query = query.filter(Notice.is_pinned == 1)
    elif filter_type != "all":
        return error("无效的筛选类型")

    total = query.count()
    items = (
        query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for n in items:
        d = NoticeOut.model_validate(n).model_dump()
        d["is_read"] = n.id in read_ids
        result.append(d)
    return paginated(result, total, page, page_size)


@router.get("/unread-count")
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import or_
    read_ids = set(r.notice_id for r in db.query(NoticeRead).filter(NoticeRead.user_id == current_user.id).all())
    now = datetime.now()
    query = db.query(Notice).filter((Notice.expire_at == None) | (Notice.expire_at > now))
    if current_user.role != "admin" and current_user.department_id:
        query = query.filter(or_(Notice.department_id == current_user.department_id, Notice.department_id == None))
    total = query.count()
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
def create_notice(data: NoticeCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    notice = Notice(title=data.title, content=data.content, notice_type=data.notice_type, is_pinned=data.is_pinned, publisher_id=current_user.id, department_id=current_user.department_id, expire_at=data.expire_at)
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return success(NoticeOut.model_validate(notice).model_dump())


@router.put("/{notice_id}")
def update_notice(notice_id: int, data: NoticeUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
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
def delete_notice(notice_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        return error("通知不存在")
    db.query(NoticeRead).filter(NoticeRead.notice_id == notice_id).delete()
    db.delete(notice)
    db.commit()
    return success(None, "删除成功")
