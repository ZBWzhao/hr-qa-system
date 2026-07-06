from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.constants.ticket_type_labels import get_ticket_type_display, normalize_ticket_type
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketOut
from app.models.ticket import Ticket
from app.models.user import User
from app.models.department import Department

router = APIRouter()


def generate_ticket_no(db: Session) -> str:
    count = db.query(Ticket).count()
    return f"TK{datetime.now().strftime('%Y%m%d')}{count + 1:04d}"


@router.get("")
def list_tickets(
    status: Optional[str] = None,
    type: Optional[str] = None,
    department_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role in ("hr", "admin"):
        query = db.query(Ticket)
        # 部门隔离：HR 只能看自己部门的工单
        if current_user.role == "hr" and current_user.department_id:
            query = query.join(User, User.id == Ticket.creator_id).filter(User.department_id == current_user.department_id)
    else:
        query = db.query(Ticket).filter(Ticket.creator_id == current_user.id)
    if status:
        query = query.filter(Ticket.status == status)
    if type:
        query = query.filter(Ticket.type == normalize_ticket_type(type))
    # Admin 可以通过 department_id 参数筛选
    if department_id is not None and current_user.role == "admin":
        if not any(j.target is User for j in query.column_descriptions):
            query = query.join(User, User.id == Ticket.creator_id)
        query = query.filter(User.department_id == department_id)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query = query.filter(or_(Ticket.title.like(kw), Ticket.ticket_no.like(kw), Ticket.description.like(kw)))
    total = query.count()
    items = query.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for t in items:
        d = TicketOut.model_validate(t).model_dump()
        creator = db.query(User).filter(User.id == t.creator_id).first()
        d["creator_name"] = creator.real_name if creator else "未知"
        d["type_label"] = get_ticket_type_display(t.type)
        if creator and creator.department_id:
            dept = db.query(Department).filter(Department.id == creator.department_id).first()
            d["department_name"] = dept.name if dept else "未分配"
            d["department_id"] = creator.department_id
        else:
            d["department_name"] = "未分配"
            d["department_id"] = None
        result.append(d)
    return paginated(result, total, page, page_size)


@router.get("/types")
def list_ticket_types(current_user: User = Depends(get_current_user)):
    """返回系统支持的全部工单类型（与智能问答工单引导一致）"""
    from app.services.ticket_intent_service import TICKET_SLOT_CONFIG
    types = [
        {"value": k, "label": v.get("display_type", k)}
        for k, v in TICKET_SLOT_CONFIG.items()
    ]
    return success(types)


@router.get("/stats")
def ticket_stats(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    query = db.query(Ticket)
    # 部门隔离：HR 只能看自己部门的工单统计
    if current_user.role == "hr" and current_user.department_id:
        query = query.join(User, User.id == Ticket.creator_id).filter(User.department_id == current_user.department_id)
    total = query.count()
    pending = query.filter(Ticket.status == "pending").count()
    processing = query.filter(Ticket.status == "processing").count()
    completed = query.filter(Ticket.status == "completed").count()
    rejected = query.filter(Ticket.status == "rejected").count()
    completed_tickets = query.filter(Ticket.status == "completed", Ticket.resolved_at != None).all()
    avg_hours = 0
    if completed_tickets:
        total_hours = sum((t.resolved_at - t.created_at).total_seconds() / 3600 for t in completed_tickets)
        avg_hours = round(total_hours / len(completed_tickets), 1)
    return success({"total": total, "pending": pending, "processing": processing, "completed": completed, "rejected": rejected, "avg_hours": avg_hours})


@router.get("/detail/{ticket_id}")
def get_ticket_detail(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """工单详情（独立路径，避免与旧版仅 PUT 的 /{ticket_id} 冲突）"""
    return get_ticket(ticket_id, current_user, db)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return error("工单不存在")
    if current_user.role not in ("hr", "admin") and ticket.creator_id != current_user.id:
        return error("无权限查看该工单", code=403)
    d = TicketOut.model_validate(ticket).model_dump()
    d["type_label"] = get_ticket_type_display(ticket.type)
    return success(d)


@router.post("")
def create_ticket(data: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    canonical_type = normalize_ticket_type(data.type)
    ticket = Ticket(
        ticket_no=generate_ticket_no(db),
        type=canonical_type,
        title=data.title,
        description=data.description,
        attachments=data.attachments,
        status="pending",
        creator_id=current_user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    d = TicketOut.model_validate(ticket).model_dump()
    d["type_label"] = get_ticket_type_display(ticket.type)
    return success(d)


@router.put("/{ticket_id}")
def update_ticket(ticket_id: int, data: TicketUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return error("工单不存在")
    if data.status is not None:
        ticket.status = data.status
        if data.status == "completed":
            ticket.resolved_at = datetime.now()
    if data.assignee_id is not None:
        ticket.assignee_id = data.assignee_id
    if data.resolve_note is not None:
        ticket.resolve_note = data.resolve_note
    db.commit()
    db.refresh(ticket)
    d = TicketOut.model_validate(ticket).model_dump()
    d["type_label"] = get_ticket_type_display(ticket.type)
    return success(d)
