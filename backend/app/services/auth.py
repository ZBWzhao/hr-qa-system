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
        status=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.status != 1:
        return None
    return user


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
