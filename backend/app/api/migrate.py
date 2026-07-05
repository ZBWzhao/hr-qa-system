"""临时迁移接口 - 数据导入完成后请删除此文件和 main.py 中的路由注册"""
from fastapi import APIRouter, Request
from sqlalchemy import text
from app.core.database import SessionLocal

router = APIRouter()


@router.post("/import-sql")
async def import_sql(request: Request):
    body = await request.body()
    sql_content = body.decode("utf-8")

    statements = [s.strip() for s in sql_content.split(";") if s.strip()]
    success = 0
    errors = []

    db = SessionLocal()
    try:
        for stmt in statements:
            upper = stmt.upper().lstrip()
            if upper.startswith("USE ") or upper.startswith("CREATE DATABASE") or upper.startswith("DROP DATABASE"):
                continue
            try:
                db.execute(text(stmt))
                success += 1
            except Exception as e:
                msg = str(e)[:150]
                errors.append(msg)
        db.commit()
    finally:
        db.close()

    return {
        "code": 0,
        "message": f"导入完成: 成功 {success} 条, 失败 {len(errors)} 条",
        "data": {"success": success, "errors": errors[:10]}
    }
