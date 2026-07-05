from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models.document import Document
from app.models.user import User

router = APIRouter()

ONBOARDING_DOCS = ["考勤管理制度", "休假与年假管理办法", "薪酬福利制度", "员工入职与转正管理办法"]

ONBOARDING_FAQS = [
    {"question": "试用期多久？", "category": "入职"},
    {"question": "报销流程是什么？", "category": "入职"},
    {"question": "上下班时间？", "category": "入职"},
]


@router.get("")
def get_onboarding(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_new = False
    if current_user.hire_date:
        is_new = (datetime.now() - current_user.hire_date).days <= 30

    docs_query = db.query(Document).filter(Document.status == "published")
    # 部门隔离：只显示自己部门的文档
    if current_user.department_id:
        docs_query = docs_query.filter(Document.department_id == current_user.department_id)
    docs = docs_query.all()
    checklist = []
    for doc in docs:
        if doc.title in ONBOARDING_DOCS:
            checklist.append({"id": doc.id, "title": doc.title, "category": doc.category, "read": False})

    return success({
        "is_new_employee": is_new,
        "hire_date": current_user.hire_date.isoformat() if current_user.hire_date else None,
        "checklist": checklist,
        "faqs": ONBOARDING_FAQS,
        "progress": 0
    })


@router.put("/checklist/{doc_id}")
def mark_read(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success(None, "已标记为已读")
