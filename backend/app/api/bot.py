from fastapi import APIRouter
from app.core.response import success

router = APIRouter()


@router.post("/webhook")
def bot_webhook(data: dict = None):
    message = ""
    if data:
        message = data.get("message", data.get("text", ""))
    return success({
        "reply": f"【IM机器人Mock】收到消息：{message}\n\n您好！我是HR智能助手，请问有什么可以帮您的？",
        "msg_type": "text"
    })
