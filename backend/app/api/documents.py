import os
import re
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.core.config import settings
from app.schemas.document import DocumentOut, ChunkOut
from app.models.document import Document, DocumentChunk, DocumentVersion
from app.models.user import User

router = APIRouter()


def split_text_to_chunks(text: str, chunk_size: int = 400) -> list:
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) > chunk_size and current:
            chunks.append(current.strip())
            current = p
        else:
            current = current + "\n\n" + p if current else p
    if current.strip():
        chunks.append(current.strip())
    final = []
    for chunk in chunks:
        if len(chunk) > chunk_size * 2:
            for i in range(0, len(chunk), chunk_size):
                final.append(chunk[i:i + chunk_size])
        else:
            final.append(chunk)
    return final


def extract_keywords(text: str) -> str:
    words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return ",".join([w for w, _ in sorted_words[:10]])


@router.get("")
def list_documents(category: Optional[str] = None, status: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    query = db.query(Document)
    if category:
        query = query.filter(Document.category == category)
    if status:
        query = query.filter(Document.status == status)
    total = query.count()
    items = query.order_by(Document.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([DocumentOut.model_validate(d).model_dump() for d in items], total, page, page_size)


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return error("文档不存在")
    return success(DocumentOut.model_validate(doc).model_dump())


@router.post("")
def create_document(title: str = Form(...), category: str = Form("other"), content_text: Optional[str] = Form(None), file: Optional[UploadFile] = File(None), current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    file_path = None
    file_type = None
    actual_content = content_text

    if file:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        file_type = file.filename.split(".")[-1] if "." in file.filename else "unknown"
        if file_type in ("txt", "md"):
            actual_content = open(file_path, "r", encoding="utf-8").read()

    doc = Document(
        title=title,
        category=category,
        file_path=file_path,
        file_type=file_type,
        content_text=actual_content,
        version="1.0",
        status="draft",
        uploader_id=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    if actual_content:
        chunks = split_text_to_chunks(actual_content)
        for i, chunk in enumerate(chunks):
            keywords = extract_keywords(chunk)
            doc_chunk = DocumentChunk(document_id=doc.id, chunk_index=i, content=chunk, keywords=keywords)
            db.add(doc_chunk)
        db.commit()

    version_record = DocumentVersion(document_id=doc.id, version="1.0", file_path=file_path, content_text=actual_content, created_by=current_user.id)
    db.add(version_record)
    db.commit()

    return success(DocumentOut.model_validate(doc).model_dump())


@router.put("/{doc_id}")
def update_document(doc_id: int, title: Optional[str] = Form(None), category: Optional[str] = Form(None), content_text: Optional[str] = Form(None), current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return error("文档不存在")
    if title is not None:
        doc.title = title
    if category is not None:
        doc.category = category
    if content_text is not None:
        doc.content_text = content_text
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
        chunks = split_text_to_chunks(content_text)
        for i, chunk in enumerate(chunks):
            keywords = extract_keywords(chunk)
            doc_chunk = DocumentChunk(document_id=doc.id, chunk_index=i, content=chunk, keywords=keywords)
            db.add(doc_chunk)
    parts = doc.version.split(".")
    doc.version = f"{parts[0]}.{int(parts[1]) + 1}"
    db.commit()
    db.refresh(doc)
    return success(DocumentOut.model_validate(doc).model_dump())


@router.delete("/{doc_id}")
def delete_document(doc_id: int, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return error("文档不存在")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    db.query(DocumentVersion).filter(DocumentVersion.document_id == doc_id).delete()
    db.delete(doc)
    db.commit()
    return success(None, "删除成功")


@router.post("/{doc_id}/publish")
def publish_document(doc_id: int, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return error("文档不存在")
    doc.status = "published"
    db.commit()
    return success(None, "发布成功")


@router.post("/{doc_id}/archive")
def archive_document(doc_id: int, current_user: User = Depends(require_roles("hr", "admin")), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return error("文档不存在")
    doc.status = "archived"
    db.commit()
    return success(None, "归档成功")


@router.get("/{doc_id}/chunks")
def get_document_chunks(doc_id: int, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).order_by(DocumentChunk.chunk_index).all()
    return success([ChunkOut.model_validate(c).model_dump() for c in chunks])


@router.get("/{doc_id}/versions")
def get_document_versions(doc_id: int, db: Session = Depends(get_db)):
    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc_id).order_by(DocumentVersion.created_at.desc()).all()
    return success([{"id": v.id, "version": v.version, "created_by": v.created_by, "created_at": v.created_at.isoformat()} for v in versions])
