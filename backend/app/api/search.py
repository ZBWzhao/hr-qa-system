import re
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success, paginated
from app.models.document import Document, DocumentChunk
from app.models.user import User

router = APIRouter()


def highlight_text(text: str, keyword: str) -> str:
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(f"<em>{keyword}</em>", text)


@router.get("")
def search_documents(keyword: str, category: Optional[str] = None, page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chunk_query = db.query(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id).filter(Document.status == "published")
    if category:
        chunk_query = chunk_query.filter(Document.category == category)

    all_results = chunk_query.all()
    matched = []
    keywords = [kw.strip() for kw in keyword.split() if kw.strip()]
    if not keywords:
        keywords = [keyword]

    for chunk, doc in all_results:
        score = 0
        for kw in keywords:
            if kw.lower() in chunk.content.lower():
                score += 1
            if chunk.keywords and kw.lower() in chunk.keywords.lower():
                score += 2
        if score > 0:
            highlighted = chunk.content
            for kw in keywords:
                highlighted = highlight_text(highlighted, kw)
            matched.append({
                "document_id": doc.id,
                "document_title": doc.title,
                "category": doc.category,
                "chunk_id": chunk.id,
                "chunk_content": chunk.content[:300],
                "highlighted_content": highlighted[:300],
                "score": score
            })

    matched.sort(key=lambda x: x["score"], reverse=True)
    total = len(matched)
    start = (page - 1) * page_size
    end = start + page_size
    items = matched[start:end]
    return paginated(items, total, page, page_size)
