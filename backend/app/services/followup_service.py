"""
上下文追问服务
用于识别和处理 follow-up 问题
"""
import re
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.qa import QARecord


# follow-up 标记词
FOLLOWUP_MARKERS = [
    '呢', '也', '一样', '多久', '限制', '材料',
    '这个', '那种', '这样', '那样', '它',
    '那么', '那', '同样', '也是', '需要'
]

# 追问开头词
FOLLOWUP_STARTERS = [
    '那', '那么', '这个', '这种', '这样', '它',
    '这种情况', '这种情况下', '这样的话'
]

# 年假相关关键词
ANNUAL_LEAVE_KEYWORDS = ['年假', '工龄', '休假', '年休假', '带薪假']

# 请假相关关键词
LEAVE_KEYWORDS = ['请假', '病假', '事假', '婚假', '产假', '丧假', '调休']

# 证明相关关键词
CERTIFY_KEYWORDS = ['在职证明', '工作证明', '收入证明', '证明开具', '证明材料']


def is_followup_question(question: str) -> bool:
    """
    判断是否是上下文追问

    Args:
        question: 用户输入

    Returns:
        是否是追问
    """
    q = question.strip()
    q_lower = q.lower()

    # 1. 代词/承接词开头
    for starter in FOLLOWUP_STARTERS:
        if q.startswith(starter):
            return True

    # 2. 短问题 + 追问标记词
    if len(q) < 15:
        for marker in FOLLOWUP_MARKERS:
            if marker in q:
                return True

    # 3. 纯数字+年/天 呢？ 格式
    if re.match(r'^\d+\s*[年天]呢?$', q):
        return True

    # 4. 工作满X年呢？格式
    if re.match(r'^工作[满够]?\d+年呢?$', q):
        return True

    # 5. X年呢？格式
    if re.match(r'^\d+年呢?$', q):
        return True

    return False


def get_recent_context(user_id: int, conversation_id: str, db: Session, limit: int = 3) -> Dict[str, Any]:
    """
    获取最近的对话上下文

    Args:
        user_id: 用户ID
        conversation_id: 会话ID
        db: 数据库会话
        limit: 获取最近几条记录

    Returns:
        上下文信息
    """
    records = db.query(QARecord).filter(
        QARecord.user_id == user_id,
        QARecord.conversation_id == conversation_id
    ).order_by(QARecord.created_at.desc()).limit(limit).all()

    if not records:
        return {
            "last_question": "",
            "last_answer_type": "",
            "last_topic": "",
            "last_answer_summary": ""
        }

    last_record = records[0]
    last_question = last_record.question or ""
    last_answer = last_record.answer or ""
    last_answer_type = last_record.answer_type or ""

    # 推断主题
    last_topic = _infer_topic(last_question, last_answer)

    # 生成回答摘要
    last_answer_summary = last_answer[:200] if last_answer else ""

    return {
        "last_question": last_question,
        "last_answer_type": last_answer_type,
        "last_topic": last_topic,
        "last_answer_summary": last_answer_summary
    }


def _infer_topic(question: str, answer: str) -> str:
    """
    从问题和回答中推断主题

    Args:
        question: 问题
        answer: 回答

    Returns:
        主题标识
    """
    text = (question + " " + answer).lower()

    # 年假主题
    for kw in ANNUAL_LEAVE_KEYWORDS:
        if kw in text:
            return "annual_leave"

    # 请假主题
    for kw in LEAVE_KEYWORDS:
        if kw in text:
            return "leave_application"

    # 证明主题
    for kw in CERTIFY_KEYWORDS:
        if kw in text:
            return "certify_ticket"

    # 考勤主题
    if any(kw in text for kw in ['考勤', '打卡', '迟到', '加班']):
        return "attendance"

    # 薪酬主题
    if any(kw in text for kw in ['工资', '薪资', '社保', '公积金', '报销']):
        return "salary"

    return "general"


def rewrite_followup_question(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    改写追问问题

    Args:
        question: 原始问题
        context: 上下文信息

    Returns:
        改写结果
    """
    q = question.strip()
    topic = context.get("last_topic", "")
    last_question = context.get("last_question", "")

    # 场景1：年假主题 + 数字追问
    if topic == "annual_leave":
        # "那工作满3年呢？" -> "工作满3年有几天年假？"
        match = re.search(r'(\d+)\s*年', q)
        if match:
            years = match.group(1)
            return {
                "is_followup": True,
                "resolved_question": f"工作满{years}年有几天年假？",
                "inherited_topic": topic,
                "context_used": True
            }

        # "16年呢？" -> "工作年限16年有几天年假？"
        if re.match(r'^\d+年呢?$', q):
            years = re.search(r'(\d+)', q).group(1)
            return {
                "is_followup": True,
                "resolved_question": f"工作年限{years}年有几天年假？",
                "inherited_topic": topic,
                "context_used": True
            }

        # "那呢？" -> 需要澄清
        if q in ['那呢？', '那呢', '呢？', '呢']:
            return {
                "is_followup": True,
                "resolved_question": "",
                "inherited_topic": topic,
                "context_used": True,
                "need_clarification": True,
                "clarification_message": "你是想问工作几年对应多少天年假吗？请补充工龄，例如'工作满3年呢'。"
            }

    # 场景2：请假主题
    if topic == "leave_application":
        # "病假也一样吗？" -> "病假请假是否也需要提前申请？"
        if '一样' in q or '也是' in q:
            # 提取新的假期类型
            leave_types = ['病假', '事假', '婚假', '产假', '丧假', '调休']
            for lt in leave_types:
                if lt in q:
                    return {
                        "is_followup": True,
                        "resolved_question": f"{lt}请假是否也需要提前申请？",
                        "inherited_topic": topic,
                        "context_used": True
                    }

        # "多久" 追问
        if '多久' in q:
            return {
                "is_followup": True,
                "resolved_question": f"请假需要提前多久申请？",
                "inherited_topic": topic,
                "context_used": True
            }

    # 场景3：证明主题 - 不改写，交给工单确认流程处理
    if topic == "certify_ticket":
        return {
            "is_followup": True,
            "resolved_question": q,
            "inherited_topic": topic,
            "context_used": True,
            "is_ticket_question": True
        }

    # 通用追问：保留原问题，但标记为追问
    return {
        "is_followup": True,
        "resolved_question": q,
        "inherited_topic": topic,
        "context_used": bool(topic)
    }
