from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, paginated
from app.models.qa import QAMiss
from app.models.user import User

router = APIRouter()


@router.post("")
def create_gap(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建知识缺口条目（允许所有用户）"""
    question = data.get("question", "").strip()
    if not question:
        return success(None, "问题不能为空")

    miss = QAMiss(user_id=current_user.id, question=question)
    db.add(miss)
    db.commit()
    db.refresh(miss)
    return success({"id": miss.id, "question": miss.question}, "知识缺口已提交")


@router.get("")
def list_gaps(resolved: int = None, page: int = 1, page_size: int = 20, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    query = db.query(QAMiss)
    if resolved is not None:
        query = query.filter(QAMiss.resolved == resolved)
    total = query.count()
    items = query.order_by(QAMiss.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for m in items:
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "question": m.question,
            "cluster_id": m.cluster_id,
            "resolved": m.resolved,
            "resolved_doc_id": m.resolved_doc_id,
            "created_at": m.created_at.isoformat()
        })
    return paginated(result, total, page, page_size)


@router.get("/stats")
def gap_stats(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    total = db.query(QAMiss).count()
    resolved = db.query(QAMiss).filter(QAMiss.resolved == 1).count()
    from sqlalchemy import func
    clusters = db.query(QAMiss.cluster_id, func.count()).filter(QAMiss.cluster_id != None).group_by(QAMiss.cluster_id).all()
    cluster_data = [{"cluster_id": c[0], "count": c[1]} for c in clusters]

    return success({
        "total": total,
        "resolved": resolved,
        "unresolved": total - resolved,
        "clusters": cluster_data,
        "suggestion": "建议针对高频未命中问题，补充相应的制度文档或FAQ"
    })


@router.put("/{miss_id}/resolve")
def resolve_gap(miss_id: int, doc_id: int = None, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    miss = db.query(QAMiss).filter(QAMiss.id == miss_id).first()
    if not miss:
        return success(None, "记录不存在")
    miss.resolved = 1
    miss.resolved_doc_id = doc_id
    db.commit()
    return success(None, "已标记为已解决")
