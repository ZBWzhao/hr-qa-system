from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    username: str
    password: str
    real_name: str
    email: Optional[str] = None
    department_id: Optional[int] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    email: Optional[str] = None
    department_id: Optional[int] = None
    role: str
    status: int
    hire_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    probation_end_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None


class UserAdminUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[int] = None
    real_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None