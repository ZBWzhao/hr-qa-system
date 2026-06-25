from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, SmallInteger
from app.core.database import Base


class User(Base):
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    real_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("sys_department.id"), nullable=True)
    role = Column(String(20), nullable=False, default="employee")
    status = Column(SmallInteger, nullable=False, default=1)
    hire_date = Column(DateTime, nullable=True)
    contract_end_date = Column(DateTime, nullable=True)
    probation_end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
