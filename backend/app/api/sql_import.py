import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/import-sql")
async def import_sql(file: UploadFile = File(...)):
    """临时端点：上传并执行 SQL 文件（用完请删除此文件）"""
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="仅支持 .sql 文件")

    try:
        content = await file.read()
        sql_text = content.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {e}")

    # 按分号分割 SQL 语句，过滤空语句
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    # 过滤掉 MySQL dump 的控制语句
    skip_prefixes = (
        "/*!", "LOCK TABLES", "UNLOCK TABLES",
        "SET @", "SET TIME_ZONE", "SET NAMES",
        "SET CHARACTER_SET", "SET FOREIGN_KEY_CHECKS",
        "SET UNIQUE_CHECKS", "SET SQL_MODE",
        "SET COLLATION_CONNECTION",
    )

    executed = 0
    errors = []

    with engine.begin() as conn:
        for stmt in statements:
            # 跳过控制语句
            if any(stmt.startswith(p) for p in skip_prefixes):
                continue
            # 跳过纯注释行
            if stmt.startswith("--"):
                continue
            try:
                conn.execute(text(stmt))
                executed += 1
            except Exception as e:
                errors.append(f"语句执行失败: {str(e)[:200]}")
                logger.warning(f"SQL执行失败: {str(e)[:200]}")

    return {
        "code": 0,
        "message": f"导入完成，成功执行 {executed} 条语句",
        "data": {
            "executed": executed,
            "errors": errors[:10] if errors else [],
            "total_errors": len(errors),
        }
    }
