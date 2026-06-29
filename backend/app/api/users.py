from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.core.security import get_password_hash
from app.schemas.user import UserOut, UserAdminUpdate
from app.models.user import User

router = APIRouter()


@router.get("")
def list_users(status: int = None, page: int = 1, page_size: int = 20, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    query = db.query(User)
    if status is not None:
        query = query.filter(User.status == status)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return paginated([UserOut.model_validate(u).model_dump() for u in items], total, page, page_size)


@router.put("/{user_id}")
def update_user(user_id: int, data: UserAdminUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error("用户不存在")
    if data.role is not None:
        user.role = data.role
    if data.status is not None:
        user.status = data.status
    if data.real_name is not None:
        user.real_name = data.real_name
    if data.email is not None:
        user.email = data.email
    if data.department_id is not None:
        user.department_id = data.department_id
    db.commit()
    db.refresh(user)
    return success(UserOut.model_validate(user).model_dump())


@router.put("/{user_id}/status")
def update_user_status(user_id: int, action: str, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """审核/启用/禁用用户 action: approve/reject/enable/disable"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error("用户不存在")
    if action == "approve":
        user.status = 1
    elif action == "reject":
        user.status = 3
    elif action == "enable":
        user.status = 1
    elif action == "disable":
        user.status = 2
    else:
        return error("无效操作")
    db.commit()
    db.refresh(user)
    return success(UserOut.model_validate(user).model_dump())


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error("用户不存在")
    user.password_hash = get_password_hash("123456")
    db.commit()
    return success(None, "密码已重置为 123456")
