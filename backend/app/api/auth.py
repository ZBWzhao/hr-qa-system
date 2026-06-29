from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success, error
from app.schemas.user import UserRegister, UserLogin, UserOut, UserUpdate
from app.services.auth import register_user, authenticate_user, create_user_token
from app.models.user import User

router = APIRouter()


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(db, data.username, data.password, data.real_name, data.email, data.department_id)
    if not user:
        return error("用户名已存在")
    return success(None, "注册申请已提交，请等待管理员审核通过后登录")


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user, err_msg = authenticate_user(db, data.username, data.password)
    if not user:
        return error(err_msg or "用户名或密码错误")
    token_data = create_user_token(user)
    return success(token_data)


@router.get("/users/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success(UserOut.model_validate(current_user).model_dump())


@router.put("/users/me")
def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.real_name is not None:
        current_user.real_name = data.real_name
    if data.email is not None:
        current_user.email = data.email
    if data.department_id is not None:
        current_user.department_id = data.department_id
    db.commit()
    db.refresh(current_user)
    return success(UserOut.model_validate(current_user).model_dump())
