from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger
from app.core.database import Base


class ReminderRule(Base):
    __tablename__ = "biz_reminder_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    rule_type = Column(String(30), nullable=False)
    trigger_days = Column(Integer, nullable=False, default=30)
    target_role = Column(String(20), nullable=True)
    channels = Column(String(100), nullable=True, default="site")
    template = Column(Text, nullable=True)
    is_active = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class ReminderLog(Base):
    __tablename__ = "biz_reminder_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(20), nullable=False, default="site")
    status = Column(String(20), nullable=False, default="sent")
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
