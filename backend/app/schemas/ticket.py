from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TicketCreate(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    attachments: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    resolve_note: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    ticket_no: str
    type: str
    title: str
    description: Optional[str] = None
    attachments: Optional[str] = None
    status: str
    creator_id: int
    assignee_id: Optional[int] = None
    resolve_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
