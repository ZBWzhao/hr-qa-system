from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.core.security import get_password_hash
from app.schemas.user import UserOut, UserAdminUpdate
from app.models.user import User

router = APIRouter()


@router.post("")
def create_user(data: dict, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """管理员创建单个用户"""
    username = data.get("username", "").strip()
    real_name = data.get("real_name", "").strip()
    email = data.get("email", "").strip()
    role = data.get("role", "employee")
    password = data.get("password", "123456")

    if not username or not real_name or not email:
        return error("工号、姓名、邮箱不能为空")

    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return error(f"工号 {username} 已存在")

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        return error(f"邮箱 {email} 已被使用")

    user = User(
        username=username,
        real_name=real_name,
        email=email,
        role=role,
        password_hash=get_password_hash(password),
        status=1  # 管理员创建的用户直接启用
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(UserOut.model_validate(user).model_dump(), "用户创建成功")


@router.post("/batch")
def batch_create_users(data: dict, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """管理员批量创建用户"""
    users_data = data.get("users", [])
    if not users_data:
        return error("用户列表为空")

    success_count = 0
    failed_count = 0
    errors = []

    for i, user_data in enumerate(users_data):
        username = user_data.get("username", "").strip()
        real_name = user_data.get("real_name", "").strip()
        email = user_data.get("email", "").strip()
        role = user_data.get("role", "employee")
        password = user_data.get("password", "123456")

        if not username or not real_name or not email:
            errors.append(f"第 {i + 1} 行：工号、姓名、邮箱不能为空")
            failed_count += 1
            continue

        # 检查用户名是否已存在
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            errors.append(f"第 {i + 1} 行：工号 {username} 已存在")
            failed_count += 1
            continue

        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            errors.append(f"第 {i + 1} 行：邮箱 {email} 已被使用")
            failed_count += 1
            continue

        try:
            user = User(
                username=username,
                real_name=real_name,
                email=email,
                role=role,
                password_hash=get_password_hash(password),
                status=1  # 管理员创建的用户直接启用
            )
            db.add(user)
            success_count += 1
        except Exception as e:
            errors.append(f"第 {i + 1} 行：创建失败 - {str(e)}")
            failed_count += 1

    db.commit()

    return success({
        "success": success_count,
        "failed": failed_count,
        "errors": errors
    }, f"导入完成：成功 {success_count} 条，失败 {failed_count} 条")


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
