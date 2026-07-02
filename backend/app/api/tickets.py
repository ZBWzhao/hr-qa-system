from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketOut
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter()


def generate_ticket_no(db: Session) -> str:
    count = db.query(Ticket).count()
    return f"TK{datetime.now().strftime('%Y%m%d')}{count + 1:04d}"


@router.get("")
def list_tickets(status: Optional[str] = None, type: Optional[str] = None, page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role in ("hr", "admin"):
        query = db.query(Ticket)
    else:
        query = db.query(Ticket).filter(Ticket.creator_id == current_user.id)
    if status:
        query = query.filter(Ticket.status == status)
    if type:
        query = query.filter(Ticket.type == type)
    total = query.count()
    items = query.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([TicketOut.model_validate(t).model_dump() for t in items], total, page, page_size)


@router.post("")
def create_ticket(data: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = Ticket(
        ticket_no=generate_ticket_no(db),
        type=data.type,
        title=data.title,
        description=data.description,
        attachments=data.attachments,
        status="pending",
        creator_id=current_user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return success(TicketOut.model_validate(ticket).model_dump())


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
    return success(TicketOut.model_validate(ticket).model_dump())


@router.get("/stats")
def ticket_stats(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    total = db.query(Ticket).count()
    pending = db.query(Ticket).filter(Ticket.status == "pending").count()
    processing = db.query(Ticket).filter(Ticket.status == "processing").count()
    completed = db.query(Ticket).filter(Ticket.status == "completed").count()
    rejected = db.query(Ticket).filter(Ticket.status == "rejected").count()
    completed_tickets = db.query(Ticket).filter(Ticket.status == "completed", Ticket.resolved_at != None).all()
    avg_hours = 0
    if completed_tickets:
        total_hours = sum((t.resolved_at - t.created_at).total_seconds() / 3600 for t in completed_tickets)
        avg_hours = round(total_hours / len(completed_tickets), 1)
    return success({"total": total, "pending": pending, "processing": processing, "completed": completed, "rejected": rejected, "avg_hours": avg_hours})
