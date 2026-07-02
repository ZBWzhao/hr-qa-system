from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.schemas.reminder import ReminderRuleCreate, ReminderRuleUpdate, ReminderRuleOut, ReminderLogOut
from app.models.reminder import ReminderRule, ReminderLog
from app.models.user import User

router = APIRouter()


@router.get("")
def list_reminders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reminders = []
    if current_user.hire_date:
        days_since_hire = (datetime.now() - current_user.hire_date).days
        if days_since_hire <= 90:
            probation_end = current_user.hire_date + timedelta(days=90)
            days_left = (probation_end - datetime.now()).days
            if days_left > 0:
                reminders.append({"type": "probation", "message": f"试用期将于{probation_end.strftime('%Y-%m-%d')}结束，还剩{days_left}天", "date": probation_end.isoformat(), "urgent": days_left <= 7})

    if current_user.contract_end_date:
        days_left = (current_user.contract_end_date - datetime.now()).days
        if 0 < days_left <= 60:
            reminders.append({"type": "contract", "message": f"合同将于{current_user.contract_end_date.strftime('%Y-%m-%d')}到期，还剩{days_left}天", "date": current_user.contract_end_date.isoformat(), "urgent": days_left <= 14})

    default_reminders = [
        {"type": "annual_leave", "message": "您今年的年假还剩5天，请在年底前使用", "date": "2026-12-31", "urgent": False},
        {"type": "training", "message": "新员工培训将于下周一举行，请准时参加", "date": "2026-07-01", "urgent": True}
    ]
    reminders.extend(default_reminders)
    return success(reminders)


@router.get("/rules")
def list_rules(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rules = db.query(ReminderRule).all()
    return success([ReminderRuleOut.model_validate(r).model_dump() for r in rules])


@router.post("/rules")
def create_rule(data: ReminderRuleCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rule = ReminderRule(name=data.name, rule_type=data.rule_type, trigger_days=data.trigger_days, target_role=data.target_role, channels=data.channels, template=data.template)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return success(ReminderRuleOut.model_validate(rule).model_dump())


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, data: ReminderRuleUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    rule = db.query(ReminderRule).filter(ReminderRule.id == rule_id).first()
    if not rule:
        return error("规则不存在")
    if data.name is not None:
        rule.name = data.name
    if data.rule_type is not None:
        rule.rule_type = data.rule_type
    if data.trigger_days is not None:
        rule.trigger_days = data.trigger_days
    if data.target_role is not None:
        rule.target_role = data.target_role
    if data.channels is not None:
        rule.channels = data.channels
    if data.template is not None:
        rule.template = data.template
    if data.is_active is not None:
        rule.is_active = data.is_active
    db.commit()
    db.refresh(rule)
    return success(ReminderRuleOut.model_validate(rule).model_dump())
