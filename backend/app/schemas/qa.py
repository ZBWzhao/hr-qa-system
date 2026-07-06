from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    action: Optional[str] = None  # confirm_submit, modify, manual_fill, transfer_to_hr
    ticket_slots: Optional[dict] = None  # 手动填写工单槽位
    context_question: Optional[str] = None  # 转人工时带入的原始咨询问题


class ChatResponse(BaseModel):
    answer: str
    answer_type: str
    source_docs: Optional[List[dict]] = None
    record_id: int
    conversation_id: Optional[str] = None


class QARecordOut(BaseModel):
    id: int
    user_id: int
    question: str
    answer: str
    answer_type: str
    source_docs: Optional[str] = None
    feedback: Optional[int] = None
    is_favorite: int
    conversation_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    keywords: Optional[str] = None
    sort_order: int = 0


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[int] = None


class FAQOut(BaseModel):
    id: int
    question: str
    answer: str
    category: Optional[str] = None
    keywords: Optional[str] = None
    view_count: int
    sort_order: int
    status: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RuleCreate(BaseModel):
    name: str
    trigger_keywords: str
    answer_template: str
    category: Optional[str] = None
    priority: int = 0


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    trigger_keywords: Optional[str] = None
    answer_template: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[int] = None


class RuleOut(BaseModel):
    id: int
    name: str
    trigger_keywords: str
    answer_template: str
    category: Optional[str] = None
    priority: int
    status: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    record_id: int
    feedback_type: str
    correction_text: Optional[str] = None


class FeedbackOut(BaseModel):
    id: int
    record_id: int
    user_id: int
    feedback_type: str
    correction_text: Optional[str] = None
    status: str
    handler_id: Optional[int] = None
    handle_note: Optional[str] = None
    ai_suggestion: Optional[str] = None
    ai_suggestion_at: Optional[datetime] = None
    created_at: datetime
    handled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedbackHandle(BaseModel):
    status: str
    handle_note: Optional[str] = None


class SearchRequest(BaseModel):
    keyword: str
    category: Optional[str] = None
    page: int = 1
    page_size: int = 20


class ConversationItem(BaseModel):
    conversation_id: str
    title: str
    last_message: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationGroup(BaseModel):
    label: str
    conversations: List[ConversationItem]