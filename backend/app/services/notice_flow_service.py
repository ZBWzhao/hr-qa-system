"""聊天内公告发布流程"""
import re
from typing import Dict, Any, Optional


NOTICE_PUBLISH_KEYWORDS = [
    "发布公告", "发通知", "发布通知", "发公告", "通知公告",
    "通知大家", "通知全体员工", "我要发公告", "我要发布公告",
    "发一个公告", "创建公告", "写公告", "发公司公告",
]


def is_notice_publish_intent(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if any(kw in q for kw in NOTICE_PUBLISH_KEYWORDS):
        return True
    if "公告" in q and any(v in q for v in ("发布", "发", "创建", "写", "通知")):
        return True
    return False


def is_notice_confirm_intent(question: str, action: Optional[str] = None) -> bool:
    if action == "confirm_submit":
        return True
    q = (question or "").strip()
    return q in ("确认发布", "确认发布公告", "直接发布", "直接发布公告", "发布", "确认")


def is_notice_cancel_intent(question: str) -> bool:
    q = (question or "").strip()
    return q in ("取消", "取消发布", "不发了", "算了")


def parse_notice_fields(question: str, filled: Dict[str, Any]) -> Dict[str, Any]:
    """从用户输入解析公告标题与内容"""
    result = dict(filled or {})
    q = (question or "").strip()
    if not q:
        return result

    title_patterns = [
        r"公告标题[：:\s]+([^,，\n]+?)(?:[,，]|公告内容|$)",
        r"标题[：:\s]+([^,，\n]+?)(?:[,，]|内容|$)",
    ]
    content_patterns = [
        r"公告内容[：:\s]+(.+)",
        r"内容[：:\s]+(.+)",
    ]

    for pat in title_patterns:
        m = re.search(pat, q, re.I)
        if m:
            result["title"] = m.group(1).strip()
            break
    for pat in content_patterns:
        m = re.search(pat, q, re.I | re.S)
        if m:
            result["content"] = m.group(1).strip()
            break

    if "title" not in result and "content" not in result:
        if "，" in q or "," in q:
            parts = re.split(r"[,，]", q, maxsplit=1)
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                if left and not result.get("title"):
                    result["title"] = re.sub(r"^(公告)?标题[：:\s]*", "", left).strip()
                if right and not result.get("content"):
                    result["content"] = re.sub(r"^(公告)?内容[：:\s]*", "", right).strip()
        elif len(q) >= 4 and not result.get("title"):
            if not result.get("content"):
                result.setdefault("title", q[: min(50, len(q))])

    return {k: v for k, v in result.items() if v}


def infer_notice_type(title: str, content: str) -> str:
    text = f"{title} {content}"
    if any(k in text for k in ("放假", "假期", "节日", "端午", "春节", "国庆")):
        return "holiday"
    if any(k in text for k in ("提醒", "截止", "清零", "尽快")):
        return "reminder"
    if any(k in text for k in ("制度", "规定", "办法", "政策", "修订")):
        return "policy"
    return "general"


def should_pin_notice(title: str, content: str) -> bool:
    text = f"{title} {content}"
    return any(k in text for k in ("紧急", "重要", "全员", "立即", "务必"))


def build_notice_confirm_answer(filled: Dict[str, Any]) -> str:
    title = filled.get("title", "")
    content = filled.get("content", "")
    ntype = infer_notice_type(title, content)
    type_label = {"holiday": "放假通知", "reminder": "提醒", "policy": "制度更新", "general": "普通通知"}.get(ntype, "普通通知")
    pinned = "是" if should_pin_notice(title, content) else "否"
    return (
        "请确认以下公告信息：\n\n"
        f"**标题：** {title}\n"
        f"**内容：** {content}\n"
        f"**类型（自动）：** {type_label}\n"
        f"**置顶：** {pinned}\n\n"
        "确认无误请回复「确认发布」，或继续补充/修改标题与内容。"
    )
