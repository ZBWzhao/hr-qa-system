from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.core.security import get_password_hash
from app.schemas.user import UserOut, UserAdminUpdate
from app.models.user import User

router = APIRouter()


@router.get("/template")
def download_template(current_user: User = Depends(require_roles("admin"))):
    """下载用户导入模板"""
    # 创建 CSV 模板内容
    template = "工号,姓名,邮箱,角色\nemp001,张三,zhangsan@company.com,employee\nhr001,李四,lisi@company.com,hr\n"

    # 转换为字节流
    output = BytesIO()
    output.write(template.encode('utf-8-sig'))  # 使用 utf-8-sig 编码以支持 Excel 打开中文
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=user_template.csv"}
    )


@router.post("/parse-file")
def parse_user_file(file: UploadFile = File(...), current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """解析上传的用户文件"""
    import csv
    import io

    # 检查文件类型
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        return error("只支持 .csv、.xlsx、.xls 格式文件")

    try:
        content = file.file.read()

        # 解析 CSV 文件
        if filename.endswith('.csv'):
            # 尝试不同编码
            text = None
            for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']:
                try:
                    text = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if not text:
                return error("文件编码无法识别，请使用 UTF-8 编码保存")

            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
        else:
            # 解析 Excel 文件
            try:
                import openpyxl
                wb = openpyxl.load_workbook(BytesIO(content), read_only=True)
                ws = wb.active
                rows = []
                for row in ws.iter_rows(values_only=True):
                    rows.append([str(cell) if cell is not None else '' for cell in row])
                wb.close()
            except ImportError:
                return error("服务器未安装 openpyxl 库，无法解析 Excel 文件")

        if len(rows) < 2:
            return error("文件内容为空或只有表头")

        # 跳过表头
        header = rows[0]
        data_rows = rows[1:]

        # 解析用户数据
        users = []
        for i, row in enumerate(data_rows):
            if len(row) < 3:
                users.append({
                    "username": "",
                    "real_name": "",
                    "email": "",
                    "role": "employee",
                    "valid": False,
                    "error": f"第 {i + 1} 行：列数不足，至少需要工号、姓名、邮箱"
                })
                continue

            username = str(row[0]).strip()
            real_name = str(row[1]).strip()
            email = str(row[2]).strip()
            role = str(row[3]).strip() if len(row) > 3 else "employee"

            # 验证角色
            valid_roles = ['employee', 'hr', 'admin']
            if role not in valid_roles:
                role = 'employee'

            # 验证数据
            valid = True
            error_msg = ""

            if not username:
                valid = False
                error_msg = "工号不能为空"
            elif not real_name:
                valid = False
                error_msg = "姓名不能为空"
            elif not email:
                valid = False
                error_msg = "邮箱不能为空"
            else:
                # 检查用户名是否已存在
                existing = db.query(User).filter(User.username == username).first()
                if existing:
                    valid = False
                    error_msg = f"工号 {username} 已存在"
                else:
                    # 检查邮箱是否已存在
                    existing_email = db.query(User).filter(User.email == email).first()
                    if existing_email:
                        valid = False
                        error_msg = f"邮箱 {email} 已被使用"

            users.append({
                "username": username,
                "real_name": real_name,
                "email": email,
                "role": role,
                "valid": valid,
                "error": error_msg
            })

        return success({"users": users})

    except Exception as e:
        return error(f"文件解析失败：{str(e)}")


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
