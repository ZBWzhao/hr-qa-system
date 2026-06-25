from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ReminderRuleCreate(BaseModel):
    name: str
    rule_type: str
    trigger_days: int = 30
    target_role: Optional[str] = None
    channels: str = "site"
    template: Optional[str] = None


class ReminderRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    trigger_days: Optional[int] = None
    target_role: Optional[str] = None
    channels: Optional[str] = None
    template: Optional[str] = None
    is_active: Optional[int] = None


class ReminderRuleOut(BaseModel):
    id: int
    name: str
    rule_type: str
    trigger_days: int
    target_role: Optional[str] = None
    channels: str
    template: Optional[str] = None
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderLogOut(BaseModel):
    id: int
    rule_id: int
    user_id: int
    message: str
    channel: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
