"""
工单多轮对话流程辅助：退出、修改、输入校验
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.llm import extract_ticket_slots_with_ai
from app.services.ticket_intent_service import TICKET_SLOT_CONFIG, detect_ticket_intent
from app.services.ticket_slot_extractor import extract_ticket_slots


TICKET_CANCEL_WORDS = {
    "取消", "不办了", "先不办", "不申请了", "放弃", "算了", "不想提交",
    "先不提交", "不用了", "不要了", "退出", "取消申请", "取消工单",
}

TICKET_MODIFY_WORDS = {"继续修改", "我要修改", "修改工单", "改一下", "重新填写"}

TICKET_CONTROL_PHRASES = {
    "手动填写", "手动填写工单", "已手动填写工单",
}

TICKET_CONFIRM_WORDS = {
    "确认", "确认提交", "提交", "提交吧", "提交工单", "可以提交", "没问题", "是的",
    "确认无误", "好的", "可以", "行", "ok", "yes", "confirm",
}

TICKET_STATUS_LABELS = {
    "pending": "待处理",
    "processing": "处理中",
    "completed": "已完成",
    "cancelled": "已取消",
}

NONSENSE_REPLIES = {
    "嗯", "啊", "哦", "呃", "哈", "呵呵", "随便", "不知道", "不清楚",
    "忘了", "没想好", "你看着办", "都行", "随便吧", "。。", "...",
}

GENERAL_QA_SIGNALS = [
    "多少", "怎么", "如何", "什么", "吗", "？", "?", "能不能", "是否可以",
    "几点", "几天", "有没有", "在哪", "哪里", "电话", "邮箱", "政策",
    "规定", "流程", "制度",
]

# 工单流程中的常见追问（不应暂停工单转普通问答）
TICKET_FOLLOWUP_SIGNALS = [
    "多久", "几天", "多长时间", "什么时候", "办理时间", "周期", "要等",
    "加急", "急", "加快", "赶时间", "来不及", "不够时间", "怎么办",
    "材料", "资料", "文件", "需要什么", "准备", "额外",
    "通知", "告知", "提醒", "会通知", "怎么知道", "联系我",
    "进度", "查看", "怎么查", "在哪看", "状态", "处理",
    "盖章", "用途", "接收", "证明",
]

# 明确与当前工单无关的 HR 主题词（出现则视为转问其它问题）
UNRELATED_HR_TOPICS = [
    "年假", "病假", "事假", "婚假", "产假", "工资", "薪资", "绩效",
    "报销", "考勤", "打卡", "迟到", "早退", "旷工", "补卡", "试用期",
    "转正", "社保", "公积金", "年终奖", "福利", "KPI", "晋升",
]

SLOT_UPDATE_PATTERNS: Dict[str, List[str]] = {
    "purpose": [
        r"用途改[为成到是]\s*(.+)",
        r"证明用途改[为成到是]\s*(.+)",
        r"用途[：:]\s*(.+)",
    ],
    "receiver": [
        r"接收单位改[为成到是]\s*(.+)",
        r"接收单位[：:]\s*(.+)",
    ],
    "need_stamp": [
        r"(需要|要|不用|不要|不)盖章",
    ],
    "expected_time": [
        r"(?:期望|完成)?时间改[为成到是]\s*(.+)",
        r"时间[：:]\s*(.+)",
    ],
}


def is_ticket_cancel_intent(question: str) -> bool:
    q = question.strip()
    if q in TICKET_CANCEL_WORDS:
        return True
    return any(p in q for p in ("取消工单", "不办证明", "先不申请", "不想开证明"))


TICKET_RESUME_WORDS = {"继续办理", "继续申请", "恢复工单", "接着办", "回到工单"}


def should_extract_slot_updates(question: str) -> bool:
    """仅当用户明确表达「修改某字段」时才做字段级更新解析"""
    q = question.strip()
    markers = (
        "改成", "改为", "修改为", "改到", "更新为",
        "用途：", "用途:", "接收单位：", "接收单位:",
        "时间改", "时间：", "时间:",
    )
    return any(m in q for m in markers)


def is_ticket_resume_intent(question: str, action: Optional[str] = None) -> bool:
    """暂停后恢复工单（继续修改/确认提交/继续办理）"""
    if is_ticket_modify_intent(question, action) or is_ticket_confirm_intent(question, action):
        return True
    q = question.strip()
    if q in TICKET_RESUME_WORDS:
        return True
    return any(p in q for p in ("继续办理", "恢复工单", "继续申请"))


def is_ticket_modify_intent(question: str, action: Optional[str] = None) -> bool:
    if action == "modify":
        return True
    q = question.strip()
    if q in TICKET_MODIFY_WORDS:
        return True
    # 「修改异常原因为…」是字段更新，不是进入修改模式
    if re.search(r"修改.+?[为:：]", q):
        return False
    return q in {"修改", "改", "改一下"}


def is_ticket_validation_intent(question: str) -> bool:
    """用户询问当前工单信息是否完整/可否提交"""
    q = question.strip().rstrip("?？.!！")
    patterns = (
        r"这样可以吗",
        r"这样行吗",
        r"这样.*吗$",
        r"合适吗",
        r"有没有问题",
        r"信息.*对吗",
        r"填.*对吗",
        r"填.*完整",
        r"没问题吗",
        r"对不对",
        r"能否提交",
        r"可以提交吗",
    )
    return any(re.search(p, q) for p in patterns)


def is_ticket_info_query(question: str) -> bool:
    """用户查询工单编号/进度等"""
    q = question.strip()
    keywords = (
        "工单号", "工单编号", "编号是多少", "单号", "ticket no",
        "哪张工单", "刚才提交", "刚提交", "提交的工单", "我的工单",
    )
    return any(k.lower() in q.lower() for k in keywords)


def is_ticket_confirm_intent(question: str, action: Optional[str] = None) -> bool:
    if action == "confirm_submit":
        return True
    q = question.strip().lower().rstrip("?？.!！")
    if q in {w.lower() for w in TICKET_CONFIRM_WORDS}:
        return True
    if is_ticket_validation_intent(question):
        return False
    if any(k in q for k in ("绩效", "申诉", "请假", "年假")):
        return False
    confirm_phrases = (
        "确认提交", "可以提交", "提交吧", "没问题", "提交工单", "那就提交", "帮我提交",
    )
    if any(p in q for p in confirm_phrases):
        return True
    if q.startswith("提交") and len(q) <= 8:
        return True
    if re.match(r"^(好的|行|可以|没问题).{0,4}(提交|吧)?$", q):
        return True
    return False


def _clean_slot_value(value: str) -> str:
    """去掉「改成/改为」等指令残留"""
    val = str(value).strip()
    val = re.sub(r"^(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*", "", val)
    val = re.sub(r"^[：:\s]+", "", val)
    return val.strip()


def _is_field_change_intent(question: str) -> bool:
    q = question.strip()
    return bool(re.search(r"(改成|改为|修改为|更新为|改到)", q))


def _regex_attendance_field_updates(question: str) -> Dict[str, Any]:
    """考勤异常字段修改的规则兜底"""
    result: Dict[str, Any] = {}
    patterns = [
        (r"(?:修改)?异常日期(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*([^,，；;]+)", "exception_date"),
        (r"(?:修改)?异常类型(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*([^,，；;]+)", "exception_type"),
        (r"(?:修改)?异常原因(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*([^,，；;]+)", "reason"),
        (r"(?:修改)?补充说明(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*([^,，；;]+)", "description"),
        (r"(?:修改)?异常日期[是为:：]+\s*([^,，；;]+)", "exception_date"),
        (r"(?:修改)?异常类型[是为:：]+\s*([^,，；;]+)", "exception_type"),
        (r"(?:修改)?异常原因[是为:：]+\s*([^,，；;]+)", "reason"),
        (r"(?:修改)?补充说明[是为:：]+\s*([^,，；;]+)", "description"),
    ]
    for pattern, slot in patterns:
        match = re.search(pattern, question)
        if match:
            val = _clean_slot_value(match.group(1))
            if val:
                result[slot] = val
    if result.get("reason") and not result.get("description"):
        result["description"] = result["reason"]
    return result


def extract_slot_field_updates(
    question: str,
    ticket_type: str,
    filled: dict | None = None,
) -> Dict[str, Any]:
    """从「XX改成YY」类表述中提取字段更新"""
    q = question.strip()
    if not q:
        return {}

    # 优先 AI 理解修改意图
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
    ai_slots = extract_ticket_slots_with_ai(q, ticket_type, config, filled)
    if ai_slots:
        return ai_slots

    if ticket_type == "attendance_exception":
        return _regex_attendance_field_updates(q)

    if ticket_type != "certify":
        return {}

    result: Dict[str, Any] = {}

    for slot, patterns in SLOT_UPDATE_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, q)
            if not match:
                continue
            if slot == "need_stamp":
                text = match.group(1)
                if text in ("不", "不用", "不要"):
                    result[slot] = False
                else:
                    result[slot] = True
            else:
                value = match.group(1).strip()
                value = re.sub(r"[，,。.!！?？]+$", "", value)
                if value:
                    result[slot] = value
            break

    return result


def is_weak_ticket_reply(question: str, extracted: Dict[str, Any]) -> bool:
    """回复是否过于模糊，无法填入工单"""
    q = question.strip()
    if not q:
        return True
    if q in NONSENSE_REPLIES:
        return True
    if len(q) <= 2 and not extracted:
        return True
    if len(q) <= 4 and not extracted and q not in {"要盖章", "不盖章", "尽快"}:
        return True
    return False


def is_ticket_flow_followup(question: str, ticket_type: str = "") -> bool:
    """用户在工单流程中追问与当前工单相关的问题"""
    q = question.strip()
    if not q:
        return False

    if any(topic in q for topic in UNRELATED_HR_TOPICS):
        return False

    pronouns = ["这个", "那个", "它", "这份", "这张", "这类"]
    if any(p in q for p in pronouns) and len(q) < 35:
        return True

    if is_ticket_validation_intent(q) or is_ticket_info_query(q):
        return True

    if any(sig in q for sig in TICKET_FOLLOWUP_SIGNALS):
        return True

    if ticket_type == "certify":
        certify_hints = [
            "签证", "盖章", "领事馆", "银行", "用途", "接收", "交给",
            "周", "月", "天内", "尽快", "底前", "日前",
        ]
        if any(h in q for h in certify_hints) and len(q) < 50:
            return True

    return False


def is_general_question_instead_of_ticket(question: str, ticket_type: str) -> bool:
    """
    用户是否在工单流程中转而提问其它 HR 问题（应暂停工单、正常问答）
    """
    q = question.strip()
    if not q:
        return False
    if is_ticket_cancel_intent(q) or is_ticket_modify_intent(q, None):
        return False
    if is_ticket_confirm_intent(q, None):
        return False
    if is_ticket_validation_intent(q):
        return False
    if is_ticket_info_query(q):
        return False

    if is_ticket_flow_followup(q, ticket_type):
        return False

    if extract_ticket_slots(q, ticket_type) or extract_slot_field_updates(q, ticket_type):
        return False

    if detect_ticket_intent(q).get("is_ticket_intent"):
        return False

    if any(topic in q for topic in UNRELATED_HR_TOPICS):
        return True

    if any(sig in q for sig in GENERAL_QA_SIGNALS):
        return True

    return False


def build_ticket_modify_prompt(
    config: dict,
    filled: dict,
) -> str:
    """进入修改模式时的引导话术"""
    lines = ["好的，已进入修改模式。当前工单信息如下：\n"]
    for slot in config["required_slots"]:
        label = config["slot_labels"].get(slot, slot)
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else ("否" if value is not None and slot in filled else "未填写")
        lines.append(f"- **{label}**：{value or '未填写'}")
    lines.append(
        "\n请直接说明要修改的内容，例如：\n"
        "- 「接收单位改成日本领事馆」\n"
        "- 「期望时间改为下周一前」\n"
        "- 或一次性重新说明全部信息\n\n"
        "如暂不需要办理，可回复「取消」；也可直接提问其它 HR 问题，系统将暂停本工单。"
    )
    return "\n".join(lines)


def build_ticket_slot_clarification(
    config: dict,
    missing_slots: List[str],
    hint: str = "",
) -> str:
    """槽位不足或回复无效时的澄清话术"""
    answer = hint or "抱歉，我没能从您的回复中提取到有效信息。"
    answer += "\n\n请补充以下信息：\n"
    for i, slot in enumerate(missing_slots, 1):
        label = config["slot_labels"].get(slot, slot)
        answer += f"{i}. {label}\n"

    if config.get("display_type") == "证明开具":
        answer += (
            "\n示例：「用来办签证，交给日本领事馆，要盖章，最好这周五前完成」\n"
            "如想先问其它问题，可直接提问；回复「取消」可放弃本次申请。"
        )
    else:
        answer += "\n如想先问其它问题，可直接提问；回复「取消」可放弃本次申请。"
    return answer


def is_ticket_control_phrase(question: str) -> bool:
    """工单流程中的操作指令，不应被当作槽位内容"""
    q = question.strip()
    if not q:
        return False
    if q in TICKET_CONTROL_PHRASES or q in TICKET_MODIFY_WORDS:
        return True
    if q in TICKET_CONFIRM_WORDS:
        return True
    if q.lower() in {w.lower() for w in TICKET_CONFIRM_WORDS}:
        return True
    return False


def normalize_ticket_filled(ticket_type: str, filled: dict) -> dict:
    """归一化工单槽位（如考勤异常自动补全补充说明）"""
    result = dict(filled)
    if ticket_type == "attendance_exception" and result.get("reason"):
        result["description"] = result["reason"]
    return result


def merge_ticket_slots(filled: dict, *updates: Dict[str, Any]) -> dict:
    merged = dict(filled)
    for patch in updates:
        for key, value in patch.items():
            if value is not None and value != "":
                merged[key] = value
    return merged


def ticket_draft_display_fields(config: dict, filled: dict) -> dict:
    """确认卡片展示字段：与手动填写表单一致，仅展示用户需填写的必填项"""
    fields = {}
    for slot in config["required_slots"]:
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else ("否" if value is not None and slot in filled else "")
        if value not in (None, ""):
            fields[slot] = _clean_slot_value(str(value)) if isinstance(value, str) else value
    return fields


def ticket_exit_to_qa_notice(ticket_type: str) -> str:
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
    return (
        f"好的，已暂停「{config['display_type']}」申请。"
        f"如需继续，可回复「继续修改」或「确认提交」。"
    )


def build_ticket_validation_answer(config: dict, filled: dict) -> str:
    """校验工单必填项并给出是否可提交的回复"""
    missing = [s for s in config["required_slots"] if not filled.get(s)]
    if missing:
        return build_ticket_slot_clarification(
            config,
            missing,
            hint="我帮您检查了当前工单信息，还有必填项未填写：",
        )

    display = config.get("display_type", "工单")
    lines = [f"我已核对您的「{display}」信息，**必填项均已填写完整**：\n"]
    for slot in config["required_slots"]:
        label = config["slot_labels"].get(slot, slot)
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else "否"
        lines.append(f"- **{label}**：{value}")
    lines.append(
        "\n如信息无误，请点击「确认提交」或回复「确认提交」；"
        "如需修改请点击「继续修改」或说明要改的内容。"
    )
    return "\n".join(lines)


def format_ticket_info_answer(ticket_record, *, include_hint: bool = True) -> str:
    """根据数据库工单记录生成编号/状态回复"""
    status = TICKET_STATUS_LABELS.get(ticket_record.status, ticket_record.status)
    lines = [
        f"您在本会话中提交的工单信息如下：\n",
        f"- **工单编号**：{ticket_record.ticket_no}",
        f"- **工单标题**：{ticket_record.title}",
        f"- **当前状态**：{status}",
    ]
    if ticket_record.created_at:
        lines.append(f"- **提交时间**：{ticket_record.created_at.strftime('%Y-%m-%d %H:%M')}")
    if include_hint:
        lines.append("\n您可以在「我的 - 人工请求」中查看详细进度。")
    return "\n".join(lines)


def answer_ticket_followup_question(
    question: str,
    ticket_type: str,
    config: dict,
    filled: dict,
    *,
    submitted: bool = False,
    ticket_record=None,
) -> str:
    """回复工单流程中（确认前/暂停中/已提交后）的用户追问"""
    q = question.strip()
    display = config.get("display_type", "工单")

    if is_ticket_info_query(q):
        if ticket_record:
            return format_ticket_info_answer(ticket_record)
        if submitted:
            return (
                "暂未在系统中查询到本对话的已提交工单记录。\n\n"
                "请稍后在「我的 - 人工请求」中查看；"
                "若此前仅收到文字确认但未显示工单编号，可能需要重新回复「确认提交」完成正式提交。"
            )
        return (
            "工单尚未正式提交，提交成功后系统会自动分配工单编号。\n\n"
            "如信息已确认无误，请点击「确认提交」或回复「确认提交」。"
        )

    status_hint = (
        "您可以在「我的 - 人工请求」中查看处理进度。"
        if submitted or ticket_record
        else "当前工单尚未提交，如信息无误请点击「确认提交」；如需修改请点击「继续修改」。"
    )

    if any(kw in q for kw in ["多久", "时间", "几天", "多长时间", "办理时间", "要等", "周期"]):
        return (
            f"「{display}」一般由 HR 根据实际工作量处理，通常建议预留 **1-3 个工作日**。\n\n"
            f"{status_hint}"
        )

    if any(kw in q for kw in ["加急", "急", "加快", "赶时间"]):
        return (
            "如需加急处理，可在工单说明中注明紧急程度，或提交后联系 HR 说明情况。"
            "HR 会根据实际情况尽量安排。\n\n"
            f"{status_hint}"
        )

    if any(kw in q for kw in ["来不及", "不够时间", "怎么办"]) and any(
        t in q for t in ["前", "周", "月", "日", "底", "deadline"]
    ):
        expected = filled.get("expected_time", "")
        time_part = f"（您期望的时间：{expected}）" if expected else ""
        return (
            f"若担心时间来不及{time_part}，建议：\n"
            "1. 尽快确认并提交工单\n"
            "2. 提交后联系 HR 说明紧急程度，申请加急\n"
            "3. HR 会根据实际情况评估是否能满足您的期望时间\n\n"
            f"{status_hint}"
        )

    if any(kw in q for kw in ["进度", "查看", "怎么查", "在哪看", "状态"]):
        return (
            "工单提交后，您可以在「我的 - 人工请求」中查看处理进度。\n\n"
            f"{status_hint}"
        )

    if any(kw in q for kw in ["修改", "改", "变更", "更正"]) and q not in TICKET_MODIFY_WORDS:
        return (
            "请直接说明要修改的内容，例如：「接收单位改成日本领事馆」或「期望时间改为下周一前」。\n\n"
            f"信息无误时可点击「确认提交」；回复「取消」可放弃申请。"
        )

    if any(kw in q for kw in ["材料", "资料", "文件", "需要什么", "准备", "额外"]):
        if ticket_type == "certify":
            return (
                "在职证明由 HR 根据内部记录直接开具，**一般不需要您额外准备材料**。"
                "如有特殊要求（如指定格式），可在提交后联系 HR 确认。\n\n"
                f"{status_hint}"
            )
        return (
            "具体所需材料请以 HR 部门要求为准。如有疑问，可在提交后联系 HR 确认。\n\n"
            f"{status_hint}"
        )

    if any(kw in q for kw in ["通知", "告知", "提醒", "会通知", "怎么知道", "联系我"]):
        return (
            "工单提交后，HR 会收到通知并尽快处理。"
            "处理完成后系统会通过消息通知您，请保持手机畅通。\n\n"
            f"{status_hint}"
        )

    return (
        f"关于「{display}」的问题，{status_hint}"
        "如有其他 HR 制度问题，也可直接提问。"
    )
