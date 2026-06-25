from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, SmallInteger
from app.core.database import Base


class Notice(Base):
    __tablename__ = "sys_notice"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    notice_type = Column(String(20), nullable=False, default="general")
    is_pinned = Column(SmallInteger, nullable=False, default=0)
    publisher_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    expire_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class NoticeRead(Base):
    __tablename__ = "sys_notice_read"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notice_id = Column(Integer, ForeignKey("sys_notice.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    read_at = Column(DateTime, nullable=False, default=datetime.now)
