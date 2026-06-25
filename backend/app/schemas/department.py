from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int
    created_at: datetime
    children: Optional[List["DepartmentOut"]] = None

    class Config:
        from_attributes = True