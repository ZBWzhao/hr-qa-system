from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, SmallInteger
from app.core.database import Base


class Comment(Base):
    __tablename__ = "biz_comment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("biz_comment.id"), nullable=True)
    like_count = Column(Integer, nullable=False, default=0)
    is_adopted = Column(SmallInteger, nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
