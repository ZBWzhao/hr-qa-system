from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from app.core.database import Base


class ConversationState(Base):
    """会话状态表，用于支持多轮澄清和槽位填充"""
    __tablename__ = "conversation_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    current_intent = Column(String(50), nullable=True)
    pending_intent = Column(String(50), nullable=True)
    required_slots = Column(Text, nullable=True)  # JSON 字符串: ["join_date", "work_years"]
    filled_slots = Column(Text, nullable=True)     # JSON 字符串: {"join_date": "2010-01-01", "work_years": 16}
    turn_count = Column(Integer, nullable=False, default=0)
    last_answer_type = Column(String(30), nullable=True)
    status = Column(String(30), nullable=False, default="active")  # active, waiting_for_slot, completed, expired
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('conversation_id', 'user_id', name='uq_conversation_user'),
    )
