"""制度文档 + 公告的统一检索与优先级判断"""
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.notice import Notice
from app.services.rag.vectorstore import search_similar
from app.services.text_splitter import extract_keywords


def search_active_notices(db: Session, question: str, limit: int = 3) -> list[dict]:
    """按关键词匹配有效公告（置顶优先）"""
    now = datetime.now()
    notices = (
        db.query(Notice)
        .filter((Notice.expire_at == None) | (Notice.expire_at > now))
        .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .all()
    )
    keywords = extract_keywords(question)
    q = question.strip()
    scored: list[tuple[int, Notice]] = []

    for notice in notices:
        text = f"{notice.title} {notice.content}"
        score = 0
        for kw in keywords:
            if kw and kw in text:
                score += 2
        if notice.title and notice.title in q:
            score += 5
        if notice.is_pinned:
            score += 1
        # 日期/时间类问题与公告内容对齐
        for token in re.findall(r"\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}", q):
            if token in text:
                score += 4
        for token in re.findall(r"下班|上班|考勤|放假|提前", q):
            if token in text:
                score += 2
        if score >= 3:
            scored.append((score, notice))

    scored.sort(key=lambda x: (-x[0], -x[1].created_at.timestamp()))
    results = []
    for score, notice in scored[:limit]:
        results.append({
            "type": "notice",
            "id": notice.id,
            "title": notice.title,
            "content": notice.content,
            "score": score,
            "is_pinned": notice.is_pinned,
            "created_at": notice.created_at,
        })
    return results


def search_document_vectors(db: Session, question: str, top_k: int = 5) -> list[dict]:
    """向量检索已发布文档 chunk，并附加文档元信息"""
    raw = search_similar(question, top_k=top_k)
    enriched = []
    for item in raw:
        meta = item.get("metadata") or {}
        doc_id = meta.get("doc_id")
        if doc_id is None:
            continue
        try:
            doc_id = int(doc_id)
        except (TypeError, ValueError):
            continue
        doc = db.query(Document).filter(Document.id == doc_id, Document.status == "published").first()
        if not doc:
            continue
        enriched.append({
            **item,
            "type": "document",
            "doc_id": doc.id,
            "doc_title": doc.title,
            "doc_updated_at": doc.updated_at,
            "doc_created_at": doc.created_at,
        })
    return enriched


def _extract_time_date_tokens(text: str) -> list[str]:
    tokens = re.findall(r"\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}|\d{1,2}点\d{0,2}分?", text or "")
    return list(dict.fromkeys(tokens))


def should_prefer_dynamic_knowledge(
    db: Session,
    question: str,
    notice_hits: list[dict],
    doc_hits: list[dict],
) -> tuple[bool, str]:
    """
    判断是否应优先使用公告/新文档，而非静态 FAQ/规则。
    返回 (是否优先, 原因: notice|document|)
    """
    if notice_hits and notice_hits[0]["score"] >= 4:
        return True, "notice"

    if not doc_hits:
        return False, ""

    top = doc_hits[0]
    chunk = top.get("content", "")
    score = float(top.get("score", 0))
    q_tokens = _extract_time_date_tokens(question)
    if q_tokens and any(t in chunk for t in q_tokens):
        return True, "document"

    doc = db.query(Document).filter(Document.id == top["doc_id"]).first()
    if doc and score >= 0.45:
        # 新上传/近期更新的文档（非仅启动时种子数据的旧版本）
        recent_cutoff = datetime.now() - timedelta(days=365)
        ref_time = doc.updated_at or doc.created_at
        if ref_time and ref_time >= recent_cutoff:
            keywords = extract_keywords(question)
            overlap = sum(1 for kw in keywords if kw and len(kw) >= 2 and kw in chunk)
            if score >= 0.5 and overlap >= 1:
                return True, "document"
            if score >= 0.65:
                return True, "document"

    if score >= 0.72:
        return True, "document"

    # 考勤/时间类：文档 chunk 含具体时间且与问题主题一致
    if score >= 0.48 and any(k in chunk for k in ("下班", "上班", "17:00", "18:00", "工作时间")):
        if any(k in question for k in ("下班", "上班", "几点", "时间", "考勤")):
            return True, "document"

    return False, ""


def search_documents_by_keyword(db: Session, question: str, limit: int = 3) -> list[dict]:
    """标题/正文关键词兜底检索（向量未命中或分数偏低时使用）"""
    docs = db.query(Document).filter(Document.status == "published").all()
    keywords = extract_keywords(question)
    q = (question or "").strip()
    scored: list[tuple[int, Document]] = []

    for doc in docs:
        title = doc.title or ""
        body = doc.content_text or ""
        text = f"{title} {body}"
        score = 0

        if title and title in q:
            score += 10
        if title:
            for part in re.findall(r"[\u4e00-\u9fff]{2,}", title):
                if part in q:
                    score += 4

        for kw in keywords:
            if kw and len(kw) >= 2 and kw in text:
                score += 2

        topic_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", q)
        for token in topic_tokens:
            if token in title:
                score += 3

        if score >= 4:
            scored.append((score, doc))

    scored.sort(key=lambda x: (-x[0], -(x[1].updated_at or x[1].created_at).timestamp()))
    results = []
    for score, doc in scored[:limit]:
        snippet = (doc.content_text or "")[:500]
        results.append({
            "type": "document",
            "doc_id": doc.id,
            "doc_title": doc.title,
            "content": snippet,
            "score": score / 10.0,
            "doc_updated_at": doc.updated_at,
            "doc_created_at": doc.created_at,
        })
    return results


def find_published_document_by_title(db: Session, title_hint: str) -> Optional[Document]:
    """按标题模糊匹配已发布文档"""
    if not title_hint or not title_hint.strip():
        return None

    hint = re.sub(r"\s+", "", title_hint.strip())
    docs = db.query(Document).filter(Document.status == "published").all()
    best: Optional[Document] = None
    best_score = 0

    for doc in docs:
        title = re.sub(r"\s+", "", doc.title or "")
        if not title:
            continue
        if hint in title or title in hint:
            return doc
        overlap = sum(1 for ch in hint if ch in title)
        ratio = overlap / max(len(hint), 1)
        if ratio >= 0.6 and overlap > best_score:
            best_score = overlap
            best = doc

    return best


def list_published_document_titles(db: Session, limit: int = 20) -> list[str]:
    docs = (
        db.query(Document)
        .filter(Document.status == "published")
        .order_by(Document.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [d.title for d in docs if d.title]


def build_knowledge_context(notice_hits: list[dict], doc_hits: list[dict], max_chars: int = 2500) -> tuple[str, list[dict]]:
    """合并公告与文档片段为 LLM 上下文"""
    parts = []
    sources = []

    for n in notice_hits[:2]:
        block = f"【公告】{n['title']}\n{n['content']}"
        parts.append(block)
        sources.append({
            "type": "notice",
            "notice_id": n["id"],
            "title": n["title"],
            "chunk": n["content"][:100],
            "score": n["score"],
        })

    for d in doc_hits[:3]:
        content = (d.get("content") or "")[:400]
        block = f"【制度文档：{d.get('doc_title', '未知')}】\n{content}"
        parts.append(block)
        sources.append({
            "type": "document",
            "doc_id": d.get("doc_id"),
            "title": d.get("doc_title"),
            "chunk": content[:100],
            "score": round(float(d.get("score", 0)), 3),
        })

    context = "\n\n".join(parts)
    if len(context) > max_chars:
        context = context[:max_chars] + "..."
    return context, sources
