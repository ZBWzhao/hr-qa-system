from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.schemas.qa import RuleCreate, RuleUpdate, RuleOut
from app.models.qa import Rule
from app.models.user import User

router = APIRouter()


@router.get("")
def list_rules(category: Optional[str] = None, page: int = 1, page_size: int = 20, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    query = db.query(Rule)
    # 部门隔离：非管理员只能看到自己部门的规则
    if current_user.role != "admin" and current_user.department_id:
        query = query.filter(Rule.department_id == current_user.department_id)
    if category:
        query = query.filter(Rule.category == category)
    total = query.count()
    items = query.order_by(Rule.priority.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([RuleOut.model_validate(r).model_dump() for r in items], total, page, page_size)


@router.get("/{rule_id}")
def get_rule(rule_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        return error("规则不存在")
    return success(RuleOut.model_validate(rule).model_dump())


@router.post("")
def create_rule(data: RuleCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rule = Rule(name=data.name, trigger_keywords=data.trigger_keywords, answer_template=data.answer_template, category=data.category, priority=data.priority, created_by=current_user.id, department_id=current_user.department_id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return success(RuleOut.model_validate(rule).model_dump())


@router.put("/{rule_id}")
def update_rule(rule_id: int, data: RuleUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        return error("规则不存在")
    if data.name is not None:
        rule.name = data.name
    if data.trigger_keywords is not None:
        rule.trigger_keywords = data.trigger_keywords
    if data.answer_template is not None:
        rule.answer_template = data.answer_template
    if data.category is not None:
        rule.category = data.category
    if data.priority is not None:
        rule.priority = data.priority
    if data.status is not None:
        rule.status = data.status
    db.commit()
    db.refresh(rule)
    return success(RuleOut.model_validate(rule).model_dump())


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        return error("规则不存在")
    db.delete(rule)
    db.commit()
    return success(None, "删除成功")
