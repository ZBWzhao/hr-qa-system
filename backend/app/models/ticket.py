from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base


class Ticket(Base):
    __tablename__ = "biz_ticket"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    creator_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("sys_user.id"), nullable=True)
    resolve_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
