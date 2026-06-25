from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, SmallInteger
from app.core.database import Base


class QARecord(Base):
    __tablename__ = "qa_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    answer_type = Column(String(20), nullable=False, default="rag")
    source_docs = Column(Text, nullable=True)
    feedback = Column(SmallInteger, nullable=True)
    is_favorite = Column(SmallInteger, nullable=False, default=0)
    conversation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class FAQ(Base):
    __tablename__ = "qa_faq"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    keywords = Column(String(500), nullable=True)
    view_count = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("sys_user.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class Rule(Base):
    __tablename__ = "qa_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    trigger_keywords = Column(String(500), nullable=False)
    answer_template = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("sys_user.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class QAFeedback(Base):
    __tablename__ = "qa_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("qa_record.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    feedback_type = Column(String(20), nullable=False)
    correction_text = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    handler_id = Column(Integer, ForeignKey("sys_user.id"), nullable=True)
    handle_note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    handled_at = Column(DateTime, nullable=True)


class QAMiss(Base):
    __tablename__ = "qa_miss"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=True)
    question = Column(Text, nullable=False)
    cluster_id = Column(Integer, nullable=True)
    resolved = Column(SmallInteger, nullable=False, default=0)
    resolved_doc_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
