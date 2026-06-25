import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, users, departments, documents, faqs, rules, search, chat, chat_history, feedback, notices, tickets, comments, recommendations, onboarding, reminders, gaps, roi, approvals, bot

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["用户管理"])
app.include_router(departments.router, prefix=f"{settings.API_V1_PREFIX}/departments", tags=["部门管理"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["文档管理"])
app.include_router(faqs.router, prefix=f"{settings.API_V1_PREFIX}/faqs", tags=["FAQ管理"])
app.include_router(rules.router, prefix=f"{settings.API_V1_PREFIX}/rules", tags=["规则问答"])
app.include_router(search.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["搜索"])
app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["智能问答"])
app.include_router(chat_history.router, prefix=f"{settings.API_V1_PREFIX}/chat/history", tags=["问答历史"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_PREFIX}/feedback", tags=["反馈"])
app.include_router(notices.router, prefix=f"{settings.API_V1_PREFIX}/notices", tags=["通知公告"])
app.include_router(tickets.router, prefix=f"{settings.API_V1_PREFIX}/tickets", tags=["工单系统"])
app.include_router(comments.router, prefix=f"{settings.API_V1_PREFIX}/comments", tags=["评论讨论"])
app.include_router(recommendations.router, prefix=f"{settings.API_V1_PREFIX}/recommendations", tags=["推荐"])
app.include_router(onboarding.router, prefix=f"{settings.API_V1_PREFIX}/onboarding", tags=["入职引导"])
app.include_router(reminders.router, prefix=f"{settings.API_V1_PREFIX}/reminders", tags=["到期提醒"])
app.include_router(gaps.router, prefix=f"{settings.API_V1_PREFIX}/gaps", tags=["知识缺口"])
app.include_router(roi.router, prefix=f"{settings.API_V1_PREFIX}/roi", tags=["ROI分析"])
app.include_router(approvals.router, prefix=f"{settings.API_V1_PREFIX}/approvals", tags=["审批Mock"])
app.include_router(bot.router, prefix=f"{settings.API_V1_PREFIX}/bot", tags=["IM机器人Mock"])


@app.get("/")
def root():
    return {"code": 0, "message": "HR Copilot API is running", "data": None}


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"code": 0, "message": "ok", "data": None}
