from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class NoticeCreate(BaseModel):
    title: str
    content: str
    notice_type: str = "general"
    is_pinned: int = 0
    expire_at: Optional[datetime] = None


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[str] = None
    is_pinned: Optional[int] = None
    expire_at: Optional[datetime] = None


class NoticeOut(BaseModel):
    id: int
    title: str
    content: str
    notice_type: str
    is_pinned: int
    publisher_id: int
    department_id: Optional[int] = None
    expire_at: Optional[datetime] = None
    created_at: datetime
    is_read: Optional[bool] = None

    class Config:
        from_attributes = True