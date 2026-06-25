from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class CommentCreate(BaseModel):
    target_type: str
    target_id: int
    content: str
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    user_id: int
    content: str
    parent_id: Optional[int] = None
    like_count: int
    is_adopted: int
    status: int
    created_at: datetime
    replies: Optional[List["CommentOut"]] = None

    class Config:
        from_attributes = True
