from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success, error
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.models.department import Department
from app.models.user import User

router = APIRouter()


def build_tree(departments: list, parent_id: Optional[int] = None) -> list:
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            node = DepartmentOut.model_validate(dept).model_dump()
            node["children"] = build_tree(departments, dept.id)
            tree.append(node)
    return tree


@router.get("")
def list_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).order_by(Department.sort_order).all()
    tree = build_tree(departments)
    return success(tree)


@router.get("/flat")
def list_departments_flat(db: Session = Depends(get_db)):
    departments = db.query(Department).order_by(Department.sort_order).all()
    return success([DepartmentOut.model_validate(d).model_dump() for d in departments])


@router.post("")
def create_department(data: DepartmentCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    dept = Department(name=data.name, parent_id=data.parent_id, sort_order=data.sort_order)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return success(DepartmentOut.model_validate(dept).model_dump())


@router.put("/{dept_id}")
def update_department(dept_id: int, data: DepartmentUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        return error("部门不存在")
    if data.name is not None:
        dept.name = data.name
    if data.parent_id is not None:
        dept.parent_id = data.parent_id
    if data.sort_order is not None:
        dept.sort_order = data.sort_order
    db.commit()
    db.refresh(dept)
    return success(DepartmentOut.model_validate(dept).model_dump())


@router.delete("/{dept_id}")
def delete_department(dept_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        return error("部门不存在")
    children = db.query(Department).filter(Department.parent_id == dept_id).count()
    if children > 0:
        return error("该部门下有子部门，无法删除")
    users = db.query(User).filter(User.department_id == dept_id).count()
    if users > 0:
        return error("该部门下有用户，无法删除")
    db.delete(dept)
    db.commit()
    return success(None, "删除成功")
