"""
工单意图识别服务
用于判断用户输入是否为工单申请意图
"""
from typing import Dict, Any


# 工单槽位配置
TICKET_SLOT_CONFIG = {
    "certify": {
        "title": "在职证明开具申请",
        "display_type": "证明开具",
        "required_slots": ["purpose", "receiver", "need_stamp", "expected_time"],
        "slot_labels": {
            "purpose": "证明用途",
            "receiver": "接收单位",
            "need_stamp": "是否需要盖章",
            "expected_time": "期望完成时间"
        }
    },
    "info_change": {
        "title": "个人信息变更申请",
        "display_type": "信息变更",
        "required_slots": ["change_item", "old_value", "new_value", "reason"],
        "slot_labels": {
            "change_item": "变更信息类型",
            "old_value": "原信息",
            "new_value": "新信息",
            "reason": "变更原因"
        }
    },
    "attendance_exception": {
        "title": "考勤异常说明",
        "display_type": "考勤异常",
        "required_slots": ["exception_date", "exception_type", "reason"],
        "slot_labels": {
            "exception_date": "异常日期",
            "exception_type": "异常类型",
            "reason": "异常原因",
            "description": "补充说明"
        }
    },
    "other": {
        "title": "HR人工处理请求",
        "display_type": "人工请求",
        "required_slots": ["issue_type", "description", "expected_time"],
        "slot_labels": {
            "issue_type": "问题类型",
            "description": "问题说明",
            "expected_time": "期望处理时间"
        }
    }
}


# 办理动词列表
ACTION_VERBS = [
    '我要', '我想', '帮我', '申请', '办理', '开具', '提交', '生成',
    '转人工', '人工处理', '需要HR', '求助HR', '找HR', '联系HR',
    '想开', '想办', '想申请', '需要办理', '需要开具', '需要申请',
    '能不能', '可以帮我', '麻烦帮我', '再开', '再办', '再提', '再申请',
]

# 未指明类型的「新工单」表达
GENERIC_NEW_TICKET_PHRASES = [
    "新工单", "新的工单", "另一个工单", "新建工单", "创建工单", "发起工单",
    "再提交一个", "再开一个", "再办一个", "再申请一个", "再来一个",
    "提交一个工单", "申请一个工单", "办理一个工单",
]


# 工单类型关键词映射
TICKET_TYPE_KEYWORDS = {
    "certify": {
        "keywords": ['在职证明', '工作证明', '收入证明', '证明', '开具证明', '开证明', '证明材料'],
        "action_phrases": ['开证明', '开具证明', '申请证明', '办证明', '办理证明', '开在职证明', '开工作证明', '开收入证明']
    },
    "info_change": {
        "keywords": ['变更', '修改', '手机号', '电话', '邮箱', '联系方式', '个人信息', '联系电话', '改手机号', '改邮箱'],
        "action_phrases": ['变更联系方式', '修改手机号', '修改邮箱', '信息变更', '改手机号', '改邮箱', '变更个人信息']
    },
    "attendance_exception": {
        "keywords": ['考勤异常', '忘记打卡', '补卡', '打卡异常', '漏打卡', '考勤说明'],
        "action_phrases": ['提交考勤异常', '提交忘记打卡', '申请补卡', '提交打卡异常', '提交考勤说明', '提交忘记打卡说明']
    }
}


def _has_specific_ticket_type(q: str) -> bool:
    """是否已指明具体工单类型"""
    for config in TICKET_TYPE_KEYWORDS.values():
        for phrase in config["action_phrases"]:
            if phrase in q:
                return True
        for kw in config["keywords"]:
            if kw in q:
                return True
    return False


def is_generic_new_ticket_intent(question: str) -> bool:
    """用户想新建工单但未说明具体类型"""
    q = question.strip()
    if not q:
        return False
    if _has_specific_ticket_type(q):
        return False
    if any(p in q for p in GENERIC_NEW_TICKET_PHRASES):
        return True
    if q in ("提交工单", "申请工单", "办理工单"):
        return True
    has_action = any(v in q for v in ACTION_VERBS)
    if has_action and "工单" in q and any(m in q for m in ("新", "再", "另一个", "一个")):
        return True
    return False


def parse_ticket_type_choice(question: str):
    """从用户选择中解析工单类型"""
    q = question.strip()
    intent = detect_ticket_intent(q)
    if intent.get("is_ticket_intent") and intent.get("ticket_type") and not intent.get("needs_type_selection"):
        return intent["ticket_type"]

    if any(k in q for k in ("在职证明", "工作证明", "收入证明", "开证明", "证明开具", "证明材料")):
        return "certify"
    if any(k in q for k in ("变更", "手机号", "邮箱", "联系方式", "个人信息", "改手机", "改邮箱")):
        return "info_change"
    if any(k in q for k in ("考勤异常", "忘记打卡", "补卡", "漏打卡", "打卡异常", "考勤说明")):
        return "attendance_exception"
    if any(k in q for k in ("转人工", "人工处理", "其他", "HR")):
        return "other"

    choice_map = {
        "1": "certify", "一": "certify", "第一种": "certify",
        "2": "info_change", "二": "info_change", "第二种": "info_change",
        "3": "attendance_exception", "三": "attendance_exception", "第三种": "attendance_exception",
        "4": "other", "四": "other", "第四种": "other",
    }
    return choice_map.get(q)


def build_ticket_type_selection_answer() -> str:
    """引导用户选择要新建的工单类型"""
    return (
        "好的，请问您要申请哪类工单？\n\n"
        "1. **在职证明 / 工作证明 / 收入证明**\n"
        "2. **个人信息变更**（手机号、邮箱等）\n"
        "3. **考勤异常说明**（忘记打卡、补卡等）\n"
        "4. **其他 HR 人工请求**\n\n"
        "请直接说明，例如「我想再开一份在职证明」或「申请信息变更」。"
        "回复「取消」可放弃本次申请。"
    )


def detect_ticket_intent(question: str) -> Dict[str, Any]:
    """
    检测用户输入是否为工单申请意图

    Args:
        question: 用户输入

    Returns:
        {
            "is_ticket_intent": bool,
            "ticket_type": str,
            "confidence": float,
            "reason": str
        }
    """
    q = question.strip()

    # 检查是否包含办理动词
    has_action_verb = any(verb in q for verb in ACTION_VERBS)

    # 如果没有办理动词，不认为是工单意图
    if not has_action_verb:
        return {
            "is_ticket_intent": False,
            "ticket_type": None,
            "confidence": 0.0,
            "reason": "无办理动词"
        }

    # 检查每种工单类型
    best_match = None
    best_confidence = 0.0

    for ticket_type, config in TICKET_TYPE_KEYWORDS.items():
        confidence = 0.0

        # 检查动作短语（高权重）
        for phrase in config["action_phrases"]:
            if phrase in q:
                confidence += 0.8
                break

        # 检查关键词
        for kw in config["keywords"]:
            if kw in q:
                confidence += 0.3
                break

        if confidence > best_confidence:
            best_confidence = confidence
            best_match = ticket_type

    # 特殊处理：转人工
    if '转人工' in q or '人工处理' in q:
        best_match = 'other'
        best_confidence = 0.9

    if best_match and best_confidence >= 0.3:
        return {
            "is_ticket_intent": True,
            "ticket_type": best_match,
            "confidence": min(best_confidence, 1.0),
            "reason": f"检测到{best_match}类型工单意图",
            "needs_type_selection": False,
        }

    if is_generic_new_ticket_intent(q):
        return {
            "is_ticket_intent": True,
            "ticket_type": None,
            "confidence": 0.7,
            "reason": "检测到新建工单意图，待选择类型",
            "needs_type_selection": True,
        }

    return {
        "is_ticket_intent": False,
        "ticket_type": None,
        "confidence": 0.0,
        "reason": "未检测到明确工单意图",
        "needs_type_selection": False,
    }
