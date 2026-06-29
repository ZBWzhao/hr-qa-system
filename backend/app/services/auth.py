from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.department import Department
from app.core.security import get_password_hash, verify_password, create_access_token


def register_user(db: Session, username: str, password: str, real_name: str, email: str = None, department_id: int = None) -> User:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return None
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        real_name=real_name,
        email=email,
        department_id=department_id,
        role="employee",
        status=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    """返回 (user, error_message) 元组"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None, "用户名或密码错误"
    if not verify_password(password, user.password_hash):
        return None, "用户名或密码错误"
    if user.status == 0:
        return None, "账号正在等待管理员审核"
    if user.status == 2:
        return None, "账号已被禁用，请联系管理员"
    if user.status == 3:
        return None, "注册申请未通过"
    if user.status != 1:
        return None, "账号状态异常"
    return user, None


def create_user_token(user: User) -> dict:
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "role": user.role,
            "department_id": user.department_id
        }
    }
