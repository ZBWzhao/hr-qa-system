import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, users, departments, documents, rules, search, chat, chat_history, conversations, feedback, notices, tickets, comments, recommendations, onboarding, reminders, gaps, roi, approvals, bot, guide, statistics

# 导入所有模型，确保 Base.metadata.create_all() 能创建所有表
from app.models import conversation_state  # noqa: F401
from app.models import knowledge_cache  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_schema_updates():
    """为已有数据库补充新增字段（幂等）"""
    from sqlalchemy import inspect, text
    from app.core.database import engine

    try:
        insp = inspect(engine)
        with engine.begin() as conn:
            # 旧版字段补充
            if "qa_feedback" in insp.get_table_names():
                cols = {c["name"] for c in insp.get_columns("qa_feedback")}
                if "ai_suggestion" not in cols:
                    conn.execute(text("ALTER TABLE qa_feedback ADD COLUMN ai_suggestion TEXT NULL"))
                if "ai_suggestion_at" not in cols:
                    conn.execute(text("ALTER TABLE qa_feedback ADD COLUMN ai_suggestion_at DATETIME NULL"))
            if "qa_faq" in insp.get_table_names():
                conn.execute(text("DROP TABLE IF EXISTS qa_faq"))

            # 部门隔离：为各表添加 department_id 字段
            dept_tables = {
                "hr_document": "department_id",
                "sys_notice": "department_id",
                "qa_rule": "department_id",
                "guide_category": "department_id",
                "qa_miss": "department_id",
                "qa_feedback": "department_id",
            }
            for table, col in dept_tables.items():
                if table in insp.get_table_names():
                    cols = {c["name"] for c in insp.get_columns(table)}
                    if col not in cols:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} INTEGER NULL"))
                        logger.info(f"已为 {table} 添加 {col} 列")

    except Exception as e:
        logger.warning("Schema update skipped: %s", e)


def ensure_ticket_type_migration():
    """将历史工单 type 统一为中文 canonical（幂等）"""
    from app.core.database import SessionLocal
    from app.constants.ticket_type_labels import migrate_ticket_types_in_db

    db = SessionLocal()
    try:
        updated = migrate_ticket_types_in_db(db)
        if updated:
            logger.info("已将 %d 条工单的 type 迁移为中文规范值", updated)
    except Exception as e:
        logger.warning("Ticket type migration skipped: %s", e)
    finally:
        db.close()


def init_rag_system():
    """初始化RAG系统：索引所有已发布文档到向量数据库"""
    try:
        from app.core.database import SessionLocal
        from app.models.document import Document, DocumentChunk
        from app.services.text_splitter import chunk_document
        from app.services.rag.vectorstore import add_documents, delete_document, get_collection_stats

        logger.info("正在初始化RAG系统...")
        db = SessionLocal()
        try:
            documents = db.query(Document).filter(Document.status == "published").all()
            logger.info(f"找到 {len(documents)} 个已发布文档")

            for doc in documents:
                delete_document(doc.id)
                chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()

                if not chunks and doc.content_text:
                    logger.info(f"  文档 [{doc.title}] 无切片，自动切分...")
                    chunk_data = chunk_document(doc.content_text)
                    for i, cd in enumerate(chunk_data):
                        chunk = DocumentChunk(
                            document_id=doc.id,
                            content=cd["content"],
                            keywords=cd["keywords"],
                            chunk_index=i
                        )
                        db.add(chunk)
                    db.commit()
                    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()

                if chunks:
                    chunk_dicts = [{"content": c.content, "keywords": c.keywords or ""} for c in chunks]
                    add_documents(doc.id, chunk_dicts, department_id=doc.department_id)
                    logger.info(f"  文档 [{doc.title}] 已索引 {len(chunks)} 个切片")

            stats = get_collection_stats()
            logger.info(f"RAG系统初始化完成! 向量数据库中共有 {stats['total_chunks']} 个向量")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"RAG系统初始化失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("HR Copilot 启动中...")
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    ensure_ticket_type_migration()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    init_rag_system()
    logger.info("HR Copilot 启动完成!")
    yield
    # 关闭时执行（可选）
    logger.info("HR Copilot 关闭中...")


app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["用户管理"])
app.include_router(departments.router, prefix=f"{settings.API_V1_PREFIX}/departments", tags=["部门管理"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["文档管理"])
app.include_router(rules.router, prefix=f"{settings.API_V1_PREFIX}/rules", tags=["规则问答"])
app.include_router(search.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["搜索"])
app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["智能问答"])
app.include_router(chat_history.router, prefix=f"{settings.API_V1_PREFIX}/chat/history", tags=["问答历史"])
app.include_router(conversations.router, prefix=f"{settings.API_V1_PREFIX}/chat/conversations", tags=["对话管理"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_PREFIX}/feedback", tags=["反馈"])
app.include_router(notices.router, prefix=f"{settings.API_V1_PREFIX}/notices", tags=["通知公告"])
app.include_router(tickets.router, prefix=f"{settings.API_V1_PREFIX}/tickets", tags=["工单系统"])
app.include_router(comments.router, prefix=f"{settings.API_V1_PREFIX}/comments", tags=["评论讨论"])
app.include_router(recommendations.router, prefix=f"{settings.API_V1_PREFIX}/recommendations", tags=["推荐"])
app.include_router(onboarding.router, prefix=f"{settings.API_V1_PREFIX}/onboarding", tags=["入职引导"])
app.include_router(reminders.router, prefix=f"{settings.API_V1_PREFIX}/reminders", tags=["到期提醒"])
app.include_router(gaps.router, prefix=f"{settings.API_V1_PREFIX}/gaps", tags=["知识缺口"])
app.include_router(guide.router, prefix=f"{settings.API_V1_PREFIX}/guide", tags=["新手指引"])
app.include_router(statistics.router, prefix=f"{settings.API_V1_PREFIX}/statistics", tags=["数据看板"])
app.include_router(roi.router, prefix=f"{settings.API_V1_PREFIX}/roi", tags=["ROI分析"])
app.include_router(approvals.router, prefix=f"{settings.API_V1_PREFIX}/approvals", tags=["审批Mock"])
app.include_router(bot.router, prefix=f"{settings.API_V1_PREFIX}/bot", tags=["IM机器人Mock"])


@app.get("/")
def root():
    return {"code": 0, "message": "HR Copilot API is running", "data": None}


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"code": 0, "message": "ok", "data": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
