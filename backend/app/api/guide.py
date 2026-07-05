"""新手指引速查 - CRUD API"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error
from app.models.user import User
from app.models.guide import GuideCategory, GuideItem

router = APIRouter()


# ==================== Pydantic Schemas ====================

class CategoryCreate(BaseModel):
    title: str
    sort_order: Optional[int] = 0


class CategoryUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None


class ItemCreate(BaseModel):
    question: str
    answer: str
    sort_order: Optional[int] = 0


class ItemUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    sort_order: Optional[int] = None


class BatchItemEntry(BaseModel):
    category_id: int
    question: str
    answer: str
    sort_order: Optional[int] = 0


class BatchItemImport(BaseModel):
    items: List[BatchItemEntry]


# ==================== 查询接口（所有用户可用） ====================

@router.get("")
def list_guide(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """新手指引目录（不含完整答案，点击条目再查）"""
    query = db.query(GuideCategory)
    # 部门隔离：非管理员只能看到自己部门的指引
    if current_user.role != "admin" and current_user.department_id:
        query = query.filter(GuideCategory.department_id == current_user.department_id)
    categories = query.order_by(GuideCategory.sort_order).all()
    result = []
    for cat in categories:
        items = db.query(GuideItem).filter(
            GuideItem.category_id == cat.id
        ).order_by(GuideItem.sort_order).all()
        result.append({
            "id": cat.id,
            "title": cat.title,
            "items": [{"id": item.id, "question": item.question} for item in items]
        })
    total = sum(len(r["items"]) for r in result)
    return success({"categories": result, "total": total})


@router.get("/items/{item_id}")
def get_guide_item(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取单条新手指引答案"""
    item = db.query(GuideItem).filter(GuideItem.id == item_id).first()
    if not item:
        return error("指引条目不存在")
    category = db.query(GuideCategory).filter(GuideCategory.id == item.category_id).first()
    return success({
        "id": item.id,
        "question": item.question,
        "answer": item.answer,
        "category": category.title if category else "",
        "category_id": item.category_id,
    })


# ==================== 管理接口（仅HR可用） ====================

@router.get("/admin/categories")
def list_categories(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """获取所有分类（含完整条目）"""
    query = db.query(GuideCategory)
    # 部门隔离：非管理员只能看到自己部门的指引
    if current_user.role != "admin" and current_user.department_id:
        query = query.filter(GuideCategory.department_id == current_user.department_id)
    categories = query.order_by(GuideCategory.sort_order).all()
    result = []
    for cat in categories:
        items = db.query(GuideItem).filter(
            GuideItem.category_id == cat.id
        ).order_by(GuideItem.sort_order).all()
        result.append({
            "id": cat.id,
            "title": cat.title,
            "sort_order": cat.sort_order,
            "items": [{
                "id": item.id,
                "question": item.question,
                "answer": item.answer,
                "sort_order": item.sort_order
            } for item in items]
        })
    return success(result)


@router.post("/admin/categories")
def create_category(data: CategoryCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """创建分类"""
    category = GuideCategory(title=data.title, sort_order=data.sort_order, department_id=current_user.department_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return success({"id": category.id, "title": category.title, "sort_order": category.sort_order})


@router.put("/admin/categories/{category_id}")
def update_category(category_id: int, data: CategoryUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """更新分类"""
    category = db.query(GuideCategory).filter(GuideCategory.id == category_id).first()
    if not category:
        return error("分类不存在")
    if data.title is not None:
        category.title = data.title
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    db.commit()
    return success({"id": category.id, "title": category.title, "sort_order": category.sort_order})


@router.delete("/admin/categories/{category_id}")
def delete_category(category_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """删除分类（级联删除条目）"""
    category = db.query(GuideCategory).filter(GuideCategory.id == category_id).first()
    if not category:
        return error("分类不存在")
    db.delete(category)
    db.commit()
    return success({"message": "删除成功"})


@router.post("/admin/categories/{category_id}/items")
def create_item(category_id: int, data: ItemCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """创建条目"""
    category = db.query(GuideCategory).filter(GuideCategory.id == category_id).first()
    if not category:
        return error("分类不存在")
    item = GuideItem(
        category_id=category_id,
        question=data.question,
        answer=data.answer,
        sort_order=data.sort_order
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success({"id": item.id, "question": item.question, "answer": item.answer, "sort_order": item.sort_order})


@router.put("/admin/items/{item_id}")
def update_item(item_id: int, data: ItemUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """更新条目"""
    item = db.query(GuideItem).filter(GuideItem.id == item_id).first()
    if not item:
        return error("条目不存在")
    if data.question is not None:
        item.question = data.question
    if data.answer is not None:
        item.answer = data.answer
    if data.sort_order is not None:
        item.sort_order = data.sort_order
    db.commit()
    return success({"id": item.id, "question": item.question, "answer": item.answer, "sort_order": item.sort_order})


@router.delete("/admin/items/{item_id}")
def delete_item(item_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """删除条目"""
    item = db.query(GuideItem).filter(GuideItem.id == item_id).first()
    if not item:
        return error("条目不存在")
    db.delete(item)
    db.commit()
    return success({"message": "删除成功"})


@router.post("/admin/items/batch")
def batch_import_items(data: BatchItemImport, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    """批量导入指引条目"""
    if not data.items:
        return error("导入列表为空")

    # 预先校验所有分类是否存在
    category_ids = {item.category_id for item in data.items}
    existing_cats = db.query(GuideCategory.id).filter(GuideCategory.id.in_(category_ids)).all()
    existing_cat_ids = {c.id for c in existing_cats}
    invalid_cats = category_ids - existing_cat_ids

    created = 0
    skipped = []

    for i, entry in enumerate(data.items):
        if entry.category_id in invalid_cats:
            skipped.append({"index": i, "question": entry.question, "reason": "分类不存在"})
            continue
        if not entry.question.strip() or not entry.answer.strip():
            skipped.append({"index": i, "question": entry.question, "reason": "问题或答案为空"})
            continue

        item = GuideItem(
            category_id=entry.category_id,
            question=entry.question.strip(),
            answer=entry.answer.strip(),
            sort_order=entry.sort_order or 0,
        )
        db.add(item)
        created += 1

    db.commit()

    return success({
        "created": created,
        "skipped": skipped,
        "total": len(data.items),
    })
