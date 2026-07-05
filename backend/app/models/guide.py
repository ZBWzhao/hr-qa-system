from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class GuideCategory(Base):
    """新员工速查指引分类"""
    __tablename__ = "guide_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False, comment="分类标题")
    department_id = Column(Integer, ForeignKey("sys_department.id"), nullable=True)
    sort_order = Column(Integer, default=0, comment="排序序号")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联条目
    items = relationship("GuideItem", back_populates="category", cascade="all, delete-orphan")


class GuideItem(Base):
    """新员工速查指引条目"""
    __tablename__ = "guide_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("guide_category.id", ondelete="CASCADE"), nullable=False)
    question = Column(String(500), nullable=False, comment="问题")
    answer = Column(Text, nullable=False, comment="答案")
    sort_order = Column(Integer, default=0, comment="排序序号")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联分类
    category = relationship("GuideCategory", back_populates="items")
