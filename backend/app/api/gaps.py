import json

from datetime import datetime

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.deps import get_current_user, require_roles

from app.core.response import success, paginated

from app.models.qa import QAMiss

from app.models.user import User

from app.models.knowledge_cache import KnowledgeAnalysisCache

from app.services.llm import generate_gap_analysis_summary



router = APIRouter()





@router.post("")

def create_gap(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    """创建知识缺口条目（允许所有用户）"""

    question = data.get("question", "").strip()

    if not question:

        return success(None, "问题不能为空")



    miss = QAMiss(user_id=current_user.id, department_id=current_user.department_id, question=question)

    db.add(miss)

    db.commit()

    db.refresh(miss)

    return success({"id": miss.id, "question": miss.question}, "知识缺口已提交")





@router.get("")

def list_gaps(resolved: int = None, page: int = 1, page_size: int = 20, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):

    query = db.query(QAMiss)
    # 部门隔离：HR 只能看自己部门的知识缺口
    if current_user.role == "hr" and current_user.department_id:
        query = query.filter(QAMiss.department_id == current_user.department_id)

    if resolved is not None:

        query = query.filter(QAMiss.resolved == resolved)

    total = query.count()

    items = query.order_by(QAMiss.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []

    for idx, m in enumerate(items):

        user = db.query(User).filter(User.id == m.user_id).first()

        result.append({

            "id": m.id,

            "user_id": m.user_id,

            "user_name": user.real_name if user else "未知",

            "username": user.username if user else "",

            "question": m.question,

            "cluster_id": m.cluster_id,

            "resolved": m.resolved,

            "resolved_doc_id": m.resolved_doc_id,

            "created_at": m.created_at.isoformat(),

            "seq": (page - 1) * page_size + idx + 1,

        })

    return paginated(result, total, page, page_size)





@router.get("/stats")

def gap_stats(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):

    query = db.query(QAMiss)
    # 部门隔离：HR 只能看自己部门的缺口统计
    if current_user.role == "hr" and current_user.department_id:
        query = query.filter(QAMiss.department_id == current_user.department_id)
    total = query.count()

    resolved = query.filter(QAMiss.resolved == 1).count()

    from sqlalchemy import func

    clusters = db.query(QAMiss.cluster_id, func.count()).filter(QAMiss.cluster_id != None).group_by(QAMiss.cluster_id).all()

    cluster_data = [{"cluster_id": c[0], "count": c[1]} for c in clusters]



    return success({

        "total": total,

        "resolved": resolved,

        "unresolved": total - resolved,

        "clusters": cluster_data,

    })





@router.get("/analysis")

def get_gap_analysis(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):

    """获取已缓存的知识缺口 AI 汇总分析（不自动调用 LLM）"""
    unresolved_query = db.query(QAMiss).filter(QAMiss.resolved == 0)
    if current_user.role == "hr" and current_user.department_id:
        unresolved_query = unresolved_query.filter(QAMiss.department_id == current_user.department_id)
    unresolved_count = unresolved_query.count()

    cache_key = "gap_summary" + (f"_dept{current_user.department_id}" if current_user.role == "hr" and current_user.department_id else "")
    cache = db.query(KnowledgeAnalysisCache).filter(KnowledgeAnalysisCache.cache_key == cache_key).first()

    if cache:

        meta = json.loads(cache.meta_json or "{}")

        if meta.get("unresolved_count") == unresolved_count and cache.content:

            return success({

                "content": cache.content,

                "cached": True,

                "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,

                "unresolved_count": unresolved_count,

            })

    return success({

        "content": "",

        "cached": False,

        "unresolved_count": unresolved_count,

    })





@router.post("/analysis/generate")

def generate_gap_analysis(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):

    """点击按钮后生成全量缺口 AI 分析并缓存"""
    unresolved_query = db.query(QAMiss).filter(QAMiss.resolved == 0)
    if current_user.role == "hr" and current_user.department_id:
        unresolved_query = unresolved_query.filter(QAMiss.department_id == current_user.department_id)

    unresolved_items = unresolved_query.order_by(QAMiss.created_at.desc()).limit(50).all()

    numbered = [{"seq": i + 1, "text": m.question} for i, m in enumerate(unresolved_items)]

    unresolved_count = unresolved_query.count()

    from app.services.llm import generate_numbered_cluster_analysis
    content = generate_numbered_cluster_analysis(numbered, "知识缺口", "未命中问题")



    cache_key = "gap_summary" + (f"_dept{current_user.department_id}" if current_user.role == "hr" and current_user.department_id else "")
    cache = db.query(KnowledgeAnalysisCache).filter(KnowledgeAnalysisCache.cache_key == cache_key).first()

    meta = json.dumps({"unresolved_count": unresolved_count, "question_sample_size": len(unresolved_items)})

    if cache:

        cache.content = content

        cache.meta_json = meta

        cache.updated_at = datetime.now()

    else:

        cache = KnowledgeAnalysisCache(

            cache_key="gap_summary",

            content=content,

            meta_json=meta,

            updated_at=datetime.now(),

        )

        db.add(cache)

    db.commit()

    db.refresh(cache)

    return success({

        "content": content,

        "cached": False,

        "updated_at": cache.updated_at.isoformat(),

        "unresolved_count": unresolved_count,

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


