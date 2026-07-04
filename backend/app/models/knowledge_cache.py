from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class KnowledgeAnalysisCache(Base):
    __tablename__ = "knowledge_analysis_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False, default="")
    meta_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
