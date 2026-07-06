#!/usr/bin/env python3
"""
一次性 SQL 导入脚本 (Railway 内部执行)
======================================
功能:
- 读取 backend/sql/hr_copilot_export.sql
- 通过 DATABASE_URL 连接 MySQL (内部地址)
- 执行 SQL 文件完成数据导入

使用方法:
cd backend
python scripts/import_sql_once.py
"""

import os
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT


BASE_DIR = Path(__file__).resolve().parent.parent
SQL_FILE = BASE_DIR / "sql" / "hr_copilot_export.sql"


def parse_database_url(url: str):
    """
    支持格式:
    mysql+pymysql://user:password@host:port/database
    mysql://user:password@host:port/database
    """
    from urllib.parse import urlparse, unquote

    if url.startswith("mysql+pymysql://"):
        url = url.replace("mysql+pymysql://", "mysql://", 1)

    parsed = urlparse(url)

    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/"),
    }


def main():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    if not SQL_FILE.exists():
        print(f"ERROR: SQL file not found: {SQL_FILE}")
        sys.exit(1)

    config = parse_database_url(database_url)

    print("Connecting to MySQL...")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")

    sql = SQL_FILE.read_text(encoding="utf-8")

    conn = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset="utf8mb4",
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )

    try:
        with conn.cursor() as cursor:
            print("Running SQL file...")
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            cursor.execute(sql)
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

        print("SQL import completed successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
