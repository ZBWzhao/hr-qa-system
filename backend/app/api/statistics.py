import hashlib
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success, error
from app.models.knowledge_cache import KnowledgeAnalysisCache
from app.models.qa import QARecord
from app.models.ticket import Ticket
from app.models.user import User
from app.models.department import Department
from app.services.llm import generate_chart_data_analysis

router = APIRouter()

CHART_TITLES = {
    "qa_trend": "问答量趋势",
    "category_dist": "咨询类别分布",
    "top_questions": "高频问题排行",
    "ticket_status": "工单状态分布",
    "ticket_by_type": "工单类型分布",
    "ticket_by_department": "工单部门分布",
    "ticket_trend": "工单提交趋势",
}


def _fingerprint(data) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _get_cache(db: Session, cache_key: str):
    return db.query(KnowledgeAnalysisCache).filter(KnowledgeAnalysisCache.cache_key == cache_key).first()


def _save_cache(db: Session, cache_key: str, content: str, meta: dict):
    fp = meta.get("fingerprint", "")
    meta_json = json.dumps(meta, ensure_ascii=False)
    cache = _get_cache(db, cache_key)
    if cache:
        cache.content = content
        cache.meta_json = meta_json
        cache.updated_at = datetime.now()
    else:
        cache = KnowledgeAnalysisCache(
            cache_key=cache_key,
            content=content,
            meta_json=meta_json,
            updated_at=datetime.now(),
        )
        db.add(cache)
    db.commit()
    db.refresh(cache)
    return cache


def _fetch_chart_data(db: Session, chart_key: str):
    month_ago = datetime.now() - timedelta(days=30)

    if chart_key == "qa_trend":
        rows = (
            db.query(func.date(QARecord.created_at), func.count())
            .filter(QARecord.created_at >= month_ago)
            .group_by(func.date(QARecord.created_at))
            .order_by(func.date(QARecord.created_at))
            .all()
        )
        return [{"date": str(d[0]), "count": d[1]} for d in rows]

    if chart_key == "category_dist":
        rows = db.query(QARecord.answer_type, func.count()).group_by(QARecord.answer_type).all()
        label_map = {
            "faq": "标准答案", "rule": "规则匹配", "rag": "文档检索", "miss": "未命中",
            "clarification": "澄清追问", "ticket_form": "工单申请", "ticket_qa": "工单咨询",
            "ticket_submitted": "工单已提交", "notice_form": "公告发布",
        }
        return [{"name": label_map.get(t, t or "其他"), "type": t, "value": c} for t, c in rows]

    if chart_key == "top_questions":
        rows = (
            db.query(QARecord.question, func.count())
            .group_by(QARecord.question)
            .order_by(func.count().desc())
            .limit(10)
            .all()
        )
        return [{"question": q, "count": c} for q, c in rows]

    if chart_key == "ticket_status":
        rows = db.query(Ticket.status, func.count()).group_by(Ticket.status).all()
        label_map = {
            "pending": "待处理", "processing": "处理中",
            "completed": "已完成", "rejected": "已驳回",
        }
        return [{"name": label_map.get(s, s), "status": s, "value": c} for s, c in rows]

    if chart_key == "ticket_by_type":
        rows = db.query(Ticket.type, func.count()).group_by(Ticket.type).all()
        type_map = {
            "certify": "证明开具", "info_change": "信息变更",
            "attendance_exception": "考勤异常", "other": "其他",
        }
        return [{"name": type_map.get(t, t), "type": t, "value": c} for t, c in rows]

    if chart_key == "ticket_by_department":
        rows = (
            db.query(Department.name, func.count())
            .join(User, User.department_id == Department.id)
            .join(Ticket, Ticket.creator_id == User.id)
            .group_by(Department.name)
            .order_by(func.count().desc())
            .all()
        )
        result = [{"name": n, "value": c} for n, c in rows]
        unassigned = (
            db.query(func.count())
            .select_from(Ticket)
            .join(User, User.id == Ticket.creator_id)
            .filter((User.department_id == None) | (User.department_id == 0))  # noqa: E711
            .scalar()
        )
        if unassigned:
            result.append({"name": "未分配部门", "value": unassigned})
        return result

    if chart_key == "ticket_trend":
        rows = (
            db.query(func.date(Ticket.created_at), func.count())
            .filter(Ticket.created_at >= month_ago)
            .group_by(func.date(Ticket.created_at))
            .order_by(func.date(Ticket.created_at))
            .all()
        )
        return [{"date": str(d[0]), "count": d[1]} for d in rows]

    return None


def _format_data_summary(chart_key: str, data) -> str:
    title = CHART_TITLES.get(chart_key, chart_key)
    if not data:
        return ""
    if chart_key in ("qa_trend", "ticket_trend"):
        lines = [f"- {d['date']}: {d['count']} 次" for d in data]
        total = sum(d["count"] for d in data)
        return f"图表：{title}\n近30日共 {total} 次\n" + "\n".join(lines)
    if chart_key == "top_questions":
        lines = [f"- {d['question'][:60]}: {d['count']} 次" for d in data]
        return f"图表：{title}\n" + "\n".join(lines)
    lines = [f"- {d.get('name', d.get('question', ''))}: {d['value']}" for d in data]
    return f"图表：{title}\n" + "\n".join(lines)


@router.get("/departments")
def get_departments(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """获取所有部门列表"""
    departments = db.query(Department).all()
    result = [{"id": d.id, "name": d.name} for d in departments]
    return success(result)


@router.get("/charts/ticket_by_type_by_dept/data")
def get_ticket_by_type_by_dept(department_id: int = None, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """按部门筛选工单类型分布"""
    type_map = {
        "certify": "证明开具", "info_change": "信息变更",
        "attendance_exception": "考勤异常", "other": "其他",
    }

    query = (
        db.query(Ticket.type, func.count())
        .join(User, User.id == Ticket.creator_id)
    )

    if department_id:
        query = query.filter(User.department_id == department_id)

    rows = query.group_by(Ticket.type).all()
    return success({"chart_key": "ticket_by_type_by_dept", "title": "工单类型分布", "data": [{"name": type_map.get(t, t), "type": t, "value": c} for t, c in rows]})


@router.get("/charts/ticket_by_dept_by_type/data")
def get_ticket_by_dept_by_type(ticket_type: str = None, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """按工单分类筛选部门分布"""
    query = (
        db.query(Department.name, func.count())
        .join(User, User.department_id == Department.id)
        .join(Ticket, Ticket.creator_id == User.id)
    )

    if ticket_type:
        query = query.filter(Ticket.type == ticket_type)

    rows = query.group_by(Department.name).order_by(func.count().desc()).all()
    result = [{"name": n, "value": c} for n, c in rows]

    # 处理未分配部门
    unassigned_query = (
        db.query(func.count())
        .select_from(Ticket)
        .join(User, User.id == Ticket.creator_id)
        .filter((User.department_id == None) | (User.department_id == 0))  # noqa: E711
    )
    if ticket_type:
        unassigned_query = unassigned_query.filter(Ticket.type == ticket_type)
    unassigned = unassigned_query.scalar()

    if unassigned:
        result.append({"name": "未分配部门", "value": unassigned})

    return success({"chart_key": "ticket_by_dept_by_type", "title": "工单部门分布", "data": result})


@router.post("/charts/ticket_by_type_by_dept/analysis/generate")
def generate_ticket_by_type_by_dept_analysis(
    department_id: int = None,
    current_user: User = Depends(require_roles("hr")),
    db: Session = Depends(get_db),
):
    """生成按部门筛选的工单类型分析"""
    type_map = {
        "certify": "证明开具", "info_change": "信息变更",
        "attendance_exception": "考勤异常", "other": "其他",
    }

    query = (
        db.query(Ticket.type, func.count())
        .join(User, User.id == Ticket.creator_id)
    )
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()
        query = query.filter(User.department_id == department_id)
        dept_name = dept.name if dept else "未知部门"
    else:
        dept_name = "全部门"

    rows = query.group_by(Ticket.type).all()
    data = [{"name": type_map.get(t, t), "type": t, "value": c} for t, c in rows]

    lines = [f"- {d['name']}: {d['value']} 单" for d in data]
    total = sum(d["value"] for d in data)
    summary = f"图表：{dept_name} - 工单类型分布\n共 {total} 单\n" + "\n".join(lines)

    content = generate_chart_data_analysis(f"{dept_name}工单类型分布", summary)
    cache_key = f"stats_ticket_by_type_dept_{department_id or 'all'}"
    fp = _fingerprint(data)
    _save_cache(db, cache_key, content, {"fingerprint": fp, "department_id": department_id})

    return success({"content": content, "cached": False, "chart_key": "ticket_by_type_by_dept", "title": f"{dept_name}工单类型分布"})


@router.post("/charts/ticket_by_dept_by_type/analysis/generate")
def generate_ticket_by_dept_by_type_analysis(
    ticket_type: str = None,
    current_user: User = Depends(require_roles("hr")),
    db: Session = Depends(get_db),
):
    """生成按工单分类筛选的部门分布分析"""
    type_map = {
        "certify": "证明开具", "info_change": "信息变更",
        "attendance_exception": "考勤异常", "other": "其他",
    }

    query = (
        db.query(Department.name, func.count())
        .join(User, User.department_id == Department.id)
        .join(Ticket, Ticket.creator_id == User.id)
    )
    if ticket_type:
        query = query.filter(Ticket.type == ticket_type)
        type_name = type_map.get(ticket_type, ticket_type)
    else:
        type_name = "全部类型"

    rows = query.group_by(Department.name).order_by(func.count().desc()).all()
    data = [{"name": n, "value": c} for n, c in rows]

    lines = [f"- {d['name']}: {d['value']} 单" for d in data]
    total = sum(d["value"] for d in data)
    summary = f"图表：{type_name} - 部门分布\n共 {total} 单\n" + "\n".join(lines)

    content = generate_chart_data_analysis(f"{type_name}部门分布", summary)
    cache_key = f"stats_ticket_by_dept_type_{ticket_type or 'all'}"
    fp = _fingerprint(data)
    _save_cache(db, cache_key, content, {"fingerprint": fp, "ticket_type": ticket_type})

    return success({"content": content, "cached": False, "chart_key": "ticket_by_dept_by_type", "title": f"{type_name}部门分布"})


@router.get("/charts/{chart_key}/data")
def get_chart_data(chart_key: str, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    if chart_key not in CHART_TITLES:
        return error("无效的图表类型")
    data = _fetch_chart_data(db, chart_key)
    return success({"chart_key": chart_key, "title": CHART_TITLES[chart_key], "data": data or []})


@router.get("/charts/{chart_key}/analysis")
def get_chart_analysis(chart_key: str, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    if chart_key not in CHART_TITLES:
        return success({"content": "", "cached": False})
    data = _fetch_chart_data(db, chart_key) or []
    fp = _fingerprint(data)
    cache_key = f"stats_{chart_key}"
    cache = _get_cache(db, cache_key)
    if cache and cache.content:
        meta = json.loads(cache.meta_json or "{}")
        if meta.get("fingerprint") == fp:
            return success({
                "content": cache.content,
                "cached": True,
                "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,
                "chart_key": chart_key,
                "title": CHART_TITLES[chart_key],
            })
    return success({
        "content": "",
        "cached": False,
        "chart_key": chart_key,
        "title": CHART_TITLES[chart_key],
    })


@router.post("/charts/{chart_key}/analysis/generate")
def generate_chart_analysis(
    chart_key: str,
    current_user: User = Depends(require_roles("hr")),
    db: Session = Depends(get_db),
):
    if chart_key not in CHART_TITLES:
        return success({"content": "无效的图表类型", "cached": False})
    data = _fetch_chart_data(db, chart_key) or []
    fp = _fingerprint(data)
    summary = _format_data_summary(chart_key, data)
    content = generate_chart_data_analysis(CHART_TITLES[chart_key], summary)
    cache_key = f"stats_{chart_key}"
    cache = _save_cache(db, cache_key, content, {"fingerprint": fp, "chart_key": chart_key})
    return success({
        "content": content,
        "cached": False,
        "updated_at": cache.updated_at.isoformat(),
        "chart_key": chart_key,
        "title": CHART_TITLES[chart_key],
    })


@router.post("/charts/top_questions/guide_analysis")
def generate_top_questions_guide_analysis(
    current_user: User = Depends(require_roles("hr")),
    db: Session = Depends(get_db),
):
    """分析高频问题，推荐可成为新员工速查指引的条目"""
    # 获取高频问题数据
    rows = (
        db.query(QARecord.question, func.count())
        .group_by(QARecord.question)
        .order_by(func.count().desc())
        .limit(20)
        .all()
    )
    questions_data = [{"question": q, "count": c} for q, c in rows]

    if not questions_data:
        return success({"content": "暂无高频问题数据", "cached": False})

    # 获取现有速查指引条目
    from app.models.guide import GuideItem
    existing_items = db.query(GuideItem.question).all()
    existing_questions = [item.question for item in existing_items]

    # 构建分析提示
    questions_text = "\n".join([f"- {q['question']}（被问 {q['count']} 次）" for q in questions_data[:15]])
    existing_text = "\n".join([f"- {q}" for q in existing_questions[:10]]) if existing_questions else "暂无"

    prompt = f"""你是一位专业的HR顾问，请分析以下高频问题，找出哪些问题适合作为"新员工速查指引"的条目。

高频问题列表（按提问次数排序）：
{questions_text}

现有速查指引条目：
{existing_text}

请从以下维度分析：
1. **问题频率**：被问次数越多，越值得收录
2. **适用人群**：是否是新员工常见问题
3. **独立性**：是否可以给出简洁明确的答案
4. **补充价值**：是否能补充现有指引的不足

你必须严格返回JSON格式，不要输出任何其他内容。格式如下：
{{
  "summary": "简要总结分析结论，一句话即可",
  "recommended": [
    {{
      "question": "问题标题",
      "reason": "推荐理由",
      "suggested_answer": "建议答案，控制在100字以内"
    }}
  ]
}}

注意：只推荐3-5个真正有价值且现有指引未覆盖的问题。"""

    from app.services.llm import call_mimo_api
    import json as _json
    import re as _re

    raw = call_mimo_api([{"role": "user", "content": prompt}], max_tokens=3000)

    # 解析AI返回的JSON
    recommendations = []
    summary = ""
    md_content = raw  # 降级用原始内容

    # 方法1：尝试直接解析整个响应为JSON
    parsed = False
    try:
        cleaned = _re.sub(r'```(?:json)?\s*', '', raw).strip()
        data = _json.loads(cleaned)
        recommended = data.get("recommended", [])
        summary = data.get("summary", "")
        for item in recommended:
            q = item.get("question", "").strip()
            r = item.get("reason", "").strip()
            a = item.get("suggested_answer", "").strip()
            if q and a:
                recommendations.append({"question": q, "reason": r, "suggested_answer": a})
        if recommendations:
            parsed = True
    except Exception:
        pass

    # 方法2：从文本中提取 JSON 对象
    if not parsed:
        try:
            cleaned = _re.sub(r'```(?:json)?\s*', '', raw).strip()
            json_match = _re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                data = _json.loads(json_match.group(0))
                recommended = data.get("recommended", [])
                summary = data.get("summary", "")
                for item in recommended:
                    q = item.get("question", "").strip()
                    r = item.get("reason", "").strip()
                    a = item.get("suggested_answer", "").strip()
                    if q and a:
                        recommendations.append({"question": q, "reason": r, "suggested_answer": a})
                if recommendations:
                    parsed = True
        except Exception:
            pass

    # 方法3：正则逐条提取（兜底）
    if not parsed:
        try:
            questions_found = _re.findall(r'"question"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            answers_found = _re.findall(r'"suggested_answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            reasons_found = _re.findall(r'"reason"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            for i, (q, a) in enumerate(zip(questions_found, answers_found)):
                r = reasons_found[i] if i < len(reasons_found) else ""
                recommendations.append({"question": q, "reason": r, "suggested_answer": a})
            summary_match = _re.search(r'"summary"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            if summary_match:
                summary = summary_match.group(1)
        except Exception:
            pass

    # 生成 Markdown 用于摘要展示
    if recommendations:
        md_parts = []
        if summary:
            md_parts.append(f"**分析摘要**：{summary}\n")
        for i, item in enumerate(recommendations, 1):
            md_parts.append(f"### {i}. {item['question']}")
            if item.get('reason'):
                md_parts.append(f"**推荐理由**：{item['reason']}")
            md_parts.append(f"**建议答案**：{item['suggested_answer']}\n")
        md_content = "\n".join(md_parts)

    # 缓存结果
    cache_key = "stats_top_questions_guide_analysis"
    fp = _fingerprint(questions_data)
    _save_cache(db, cache_key, md_content, {"fingerprint": fp, "type": "guide_analysis"})

    return success({
        "content": md_content,
        "recommendations": recommendations,
        "cached": False,
        "chart_key": "top_questions_guide_analysis",
        "title": "高频问题速查指引推荐",
    })
