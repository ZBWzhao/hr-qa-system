from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    category: str = "other"
    content_text: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content_text: Optional[str] = None


class DocumentOut(BaseModel):
    id: int
    title: str
    category: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    content_text: Optional[str] = None
    version: str
    status: str
    uploader_id: int
    department_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    keywords: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True