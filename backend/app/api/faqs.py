from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.schemas.qa import FAQCreate, FAQUpdate, FAQOut
from app.models.qa import FAQ
from app.models.user import User

router = APIRouter()


@router.get("")
def list_faqs(category: Optional[str] = None, keyword: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    query = db.query(FAQ).filter(FAQ.status == 1)
    if category:
        query = query.filter(FAQ.category == category)
    if keyword:
        query = query.filter(FAQ.question.contains(keyword) | FAQ.keywords.contains(keyword))
    total = query.count()
    items = query.order_by(FAQ.sort_order, FAQ.view_count.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([FAQOut.model_validate(f).model_dump() for f in items], total, page, page_size)


@router.get("/all")
def list_all_faqs(page: int = 1, page_size: int = 20, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    query = db.query(FAQ)
    total = query.count()
    items = query.order_by(FAQ.sort_order.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([FAQOut.model_validate(f).model_dump() for f in items], total, page, page_size)


@router.get("/{faq_id}")
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error("FAQ不存在")
    faq.view_count += 1
    db.commit()
    return success(FAQOut.model_validate(faq).model_dump())


@router.post("")
def create_faq(data: FAQCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    faq = FAQ(question=data.question, answer=data.answer, category=data.category, keywords=data.keywords, sort_order=data.sort_order, created_by=current_user.id)
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return success(FAQOut.model_validate(faq).model_dump())


@router.put("/{faq_id}")
def update_faq(faq_id: int, data: FAQUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error("FAQ不存在")
    if data.question is not None:
        faq.question = data.question
    if data.answer is not None:
        faq.answer = data.answer
    if data.category is not None:
        faq.category = data.category
    if data.keywords is not None:
        faq.keywords = data.keywords
    if data.sort_order is not None:
        faq.sort_order = data.sort_order
    if data.status is not None:
        faq.status = data.status
    db.commit()
    db.refresh(faq)
    return success(FAQOut.model_validate(faq).model_dump())


@router.delete("/{faq_id}")
def delete_faq(faq_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error("FAQ不存在")
    db.delete(faq)
    db.commit()
    return success(None, "删除成功")
