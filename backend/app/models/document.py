from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base


class Document(Base):
    __tablename__ = "hr_document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, default="other")
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
    content_text = Column(Text, nullable=True)
    version = Column(String(20), nullable=False, default="1.0")
    status = Column(String(20), nullable=False, default="draft")
    uploader_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class DocumentVersion(Base):
    __tablename__ = "hr_document_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("hr_document.id"), nullable=False)
    version = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class DocumentChunk(Base):
    __tablename__ = "hr_document_chunk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("hr_document.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(String(500), nullable=True)
    vector_mock = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
