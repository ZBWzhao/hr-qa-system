"""
上下文追问服务
用于识别和处理 follow-up 问题
"""
import re
from typing import Dict, Any, List
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

# 考勤子话题
ATTENDANCE_SUBTOPICS = {
    '迟到': '迟到怎么处理？',
    '早退': '早退怎么处理？',
    '旷工': '旷工怎么处理？',
    '加班': '加班怎么处理？',
    '忘记打卡': '忘记打卡怎么处理？',
    '补卡': '补卡规则是什么？',
}

# 不参与主题推断的回答类型（澄清模板含多个领域词，不能用来推断主题）
SKIP_TOPIC_ANSWER_TYPES = {'miss', 'error', 'clarification'}

# 工单相关回答类型 → 证明/工单主题
TICKET_ANSWER_TYPES = {
    'ticket_clarification', 'ticket_confirm', 'ticket_submitted', 'ticket_qa',
}

# 中文数字映射
_CN_NUM_MAP = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '两': 2, '俩': 2,
}

# 用户问题中明确询问年假的表达（不含 mere「X年呢」）
EXPLICIT_ANNUAL_LEAVE_QUESTION_KEYWORDS = [
    '年假', '年休假', '带薪年假', '带薪假', '休假制度', '年假标准',
    '年假天数', '年假政策', '年假规定', '年假怎么', '年假如何', '年假计算',
    '有几天假', '几天假', '多少天假', '能休几天', '可以休几天',
]

# 工龄/年假追问模式
WORK_YEARS_FOLLOWUP_PATTERN = re.compile(
    r'(?:'
    r'(\d+)\s*年\s*(以上|以内|不满|满)?'
    r'|'
    r'([一二三四五六七八九十两俩]+)\s*年\s*(以上|以内|不满|满)?'
    r')'
)


def _chinese_to_number(cn: str) -> int | None:
    """解析常见中文数字，如：三、十、二十、二十三"""
    cn = cn.strip()
    if not cn:
        return None
    if cn.isdigit():
        return int(cn)

    if cn == '十':
        return 10
    if cn.startswith('十') and len(cn) == 2:
        return 10 + _CN_NUM_MAP.get(cn[1], 0)
    if cn.endswith('十') and len(cn) == 2:
        return _CN_NUM_MAP.get(cn[0], 0) * 10
    if '十' in cn:
        parts = cn.split('十')
        tens = _CN_NUM_MAP.get(parts[0], 0) if parts[0] else 1
        ones = _CN_NUM_MAP.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return tens * 10 + ones
    if len(cn) == 1 and cn in _CN_NUM_MAP:
        return _CN_NUM_MAP[cn]
    return None


def _parse_years_expression(text: str) -> tuple[int, str] | None:
    """
    从文本解析工龄表达，返回 (年数, 修饰词)
    修饰词：'' | '以上' | '以内' | '满'
    """
    match = WORK_YEARS_FOLLOWUP_PATTERN.search(text)
    if not match:
        return None

    if match.group(1) is not None:
        years = int(match.group(1))
        modifier = (match.group(2) or '').strip()
    else:
        years = _chinese_to_number(match.group(3) or '')
        modifier = (match.group(4) or '').strip()
        if years is None:
            return None

    if not (0 <= years <= 60):
        return None
    return years, modifier


def _is_work_years_related_followup(question: str) -> bool:
    """是否是与工龄/年数相关的追问"""
    return _parse_years_expression(question) is not None or is_year_number_followup(question)


def _calc_annual_leave_days(work_years: int) -> int:
    """按公司制度计算年假天数"""
    if work_years < 1:
        return 0
    if work_years < 10:
        return 5
    if work_years < 20:
        return 10
    return 15


def _build_annual_leave_years_question(years: int, modifier: str) -> str:
    """将工龄表达改写成完整年假问题"""
    if modifier == '以上':
        return f"工作年限{years}年以上有几天年假？"
    if modifier in ('以内', '不满'):
        return f"工作年限{years}年{modifier}有几天年假？"
    if modifier == '满':
        return f"工作满{years}年有几天年假？"
    return f"工作满{years}年有几天年假？"


def is_followup_question(question: str) -> bool:
    """判断是否是上下文追问"""
    q = question.strip()

    for starter in FOLLOWUP_STARTERS:
        if q.startswith(starter):
            return True

    if len(q) < 15:
        for marker in FOLLOWUP_MARKERS:
            if marker in q:
                return True

    if re.match(r'^\d+\s*[年天]呢?[？?]?$', q):
        return True

    if re.match(r'^工作[满够]?\s*\d+\s*年呢?[？?]?$', q):
        return True

    if re.match(r'^\d+\s*年呢?[？?]?$', q):
        return True

    if WORK_YEARS_FOLLOWUP_PATTERN.search(q) and len(q) < 20:
        return True

    return False


def is_year_number_followup(question: str) -> bool:
    """判断是否是含数字/工龄的短追问"""
    q = question.strip()
    if _parse_years_expression(q):
        return True
    if re.search(r'\d+\s*年', q):
        return True
    if re.match(r'^[那]?\s*\d+\s*年呢?[？?]?$', q):
        return True
    if re.match(r'^工作[满够]?\s*\d+\s*年呢?[？?]?$', q):
        return True
    return False


def is_vague_pronoun_followup(question: str) -> bool:
    """判断是否是含指代词的短追问"""
    q = question.strip()
    if len(q) > 20:
        return False
    pronouns = ['这个', '那个', '它', '那样', '这样', '那种']
    return any(p in q for p in pronouns)


def is_ambiguous_followup_without_keywords(question: str) -> bool:
    """无明确领域词的模糊短追问（才需要澄清）"""
    if _try_standalone_expand(question.strip()):
        return False
    return is_year_number_followup(question) or is_vague_pronoun_followup(question)


def _try_standalone_expand(q: str) -> Dict[str, Any]:
    """
    从追问本身提取明确领域词并展开为完整问题（无需对话历史）
    例如：「那迟到呢？」→「迟到怎么处理？」
    """
    for keyword, resolved in ATTENDANCE_SUBTOPICS.items():
        if keyword in q:
            return {
                "is_followup": True,
                "resolved_question": resolved,
                "inherited_topic": "attendance",
                "context_used": False,
                "standalone_expand": True,
            }

    for lt in LEAVE_KEYWORDS:
        if lt in q:
            return {
                "is_followup": True,
                "resolved_question": f"{lt}请假有什么规定？",
                "inherited_topic": "leave_application",
                "context_used": False,
                "standalone_expand": True,
            }

    if any(kw in q for kw in ANNUAL_LEAVE_KEYWORDS):
        return {
            "is_followup": True,
            "resolved_question": q.replace("那", "").replace("呢", "").strip() + "有几天年假？"
            if "年假" not in q else q,
            "inherited_topic": "annual_leave",
            "context_used": False,
            "standalone_expand": True,
        }

    return {}


def expand_clarification_choice(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    用户回复澄清选项（如「工龄福利」）时，展开为完整问句并继承主题
    """
    if context.get("last_answer_type") != "clarification":
        return {}

    q = question.strip()
    if len(q) > 20:
        return {}

    # 从最近用户问题中提取年数上下文（如「那 3 年呢？」）
    years_expr = None
    for uq in reversed(context.get("recent_user_questions", [])):
        parsed = _parse_years_expression(uq)
        if parsed:
            years_expr = parsed
            break

    years_text = ""
    if years_expr:
        years, modifier = years_expr
        if modifier == "以上":
            years_text = f"{years}年以上"
        elif modifier:
            years_text = f"{years}年{modifier}"
        else:
            years_text = f"{years}年"

    if "工龄福利" in q:
        resolved = (
            f"工作{years_text}有什么工龄福利？"
            if years_text
            else "公司工龄福利有什么规定？"
        )
        return {
            "is_followup": True,
            "resolved_question": resolved,
            "inherited_topic": "salary_welfare",
            "context_used": True,
        }

    if any(k in q for k in ("年假", "年假天数")):
        resolved = (
            f"工作满{years_text}有几天年假？"
            if years_text
            else "我有多少天年假？"
        )
        return {
            "is_followup": True,
            "resolved_question": resolved,
            "inherited_topic": "annual_leave",
            "context_used": True,
            "explicit_annual_leave_intent": True,
        }

    if any(k in q for k in ("试用", "转正", "续签")):
        resolved = (
            f"工作满{years_text}转正有什么规定？"
            if years_text
            else "试用期和转正有什么规定？"
        )
        return {
            "is_followup": True,
            "resolved_question": resolved,
            "inherited_topic": "probation",
            "context_used": True,
        }

    return {}


def _user_question_explicit_annual_leave(question: str) -> bool:
    """用户问题中是否明确提到年假（纯「X年呢」不算）"""
    q = (question or "").strip()
    if not q:
        return False
    return any(kw in q for kw in EXPLICIT_ANNUAL_LEAVE_QUESTION_KEYWORDS)


def _has_explicit_annual_leave_intent(context: Dict[str, Any]) -> bool:
    """会话中是否已有用户明确问过年假"""
    if context.get("explicit_annual_leave_intent"):
        return True
    for q in context.get("recent_user_questions", []):
        if _user_question_explicit_annual_leave(q):
            return True
    return False


def build_year_followup_clarification(question: str) -> str:
    """工龄/年数短追问的统一澄清话术"""
    q = question.strip()
    if re.search(r'工作[满够]', q):
        return (
            "你是想问年假天数、工龄福利，还是转正/续签制度？\n\n"
            "例如：「工作满3年有几天年假？」"
        )

    parsed = _parse_years_expression(q)
    if parsed:
        years, modifier = parsed
        if modifier == '以上':
            years_text = f"{years}年以上"
        elif modifier:
            years_text = f"{years}年{modifier}"
        else:
            years_text = f"{years}年"
        prefix = f"你提到的「{years_text}」"
    elif '年' in q:
        prefix = "你提到的「年」"
    else:
        prefix = "你提到的内容"

    return (
        f"{prefix}需要补充上下文。\n\n"
        "你是想问年假天数、工龄福利、试用/转正，还是其他制度？\n"
        "例如：「工作满3年有几天年假？」"
    )


def build_pronoun_followup_clarification(context: Dict[str, Any]) -> str:
    """指代追问的澄清话术"""
    if context.get("has_recent_year_followup"):
        return (
            "你提到的「这个/那」需要补充上下文。\n\n"
            "你是想问年假天数、工龄福利、试用/转正，还是其他制度？\n"
            "例如：「工作满3年有几天年假？」"
        )
    return build_no_context_clarification("这个")


def build_no_context_clarification(question: str) -> str:
    """无上下文短追问的澄清话术"""
    if _is_work_years_related_followup(question):
        return build_year_followup_clarification(question)

    q = question.strip()
    year_match = re.search(r'(\d+)\s*年', q)
    if year_match or '年' in q:
        return build_year_followup_clarification(q)

    return (
        "你这个问题需要结合上下文才能准确回答。\n\n"
        "请补充你想了解的具体内容，例如：\n"
        "1. 年假天数或工龄福利\n"
        "2. 考勤、迟到、补卡相关规定\n"
        "3. 请假、试用期或其他制度"
    )


def build_incompatible_year_clarification() -> str:
    """追问含「年」但与上一轮主题不兼容时的澄清话术"""
    return build_year_followup_clarification("年")


def is_unresolved_followup(question: str, is_followup: bool, followup_context: Dict[str, Any]) -> bool:
    """判断追问是否未能有效改写，不应写入 qa_miss"""
    if not is_followup_question(question):
        return False
    if not is_followup:
        return True
    if followup_context.get("need_clarification"):
        return True
    resolved = (followup_context.get("resolved_question") or "").strip()
    original = question.strip()
    if not resolved or resolved == original:
        topic = followup_context.get("inherited_topic", "")
        if topic in ("general", ""):
            return True
        if topic == "annual_leave" and _is_work_years_related_followup(question):
            return True
    return False


def was_followup_rewritten(question: str, followup_context: Dict[str, Any]) -> bool:
    """判断追问是否已成功改写为完整问题"""
    if not followup_context.get("is_followup"):
        return False
    resolved = (followup_context.get("resolved_question") or "").strip()
    return bool(resolved) and resolved != question.strip()


def get_attendance_policy_answer(resolved_question: str) -> Dict[str, Any]:
    """
    考勤主题追问的内置政策回答（RAG/规则未命中时的兜底）
    依据 init_db 中《考勤管理制度》条款
    """
    q = resolved_question
    source_docs = [{"source": "考勤制度", "document": "考勤管理制度", "name": "迟到早退规则"}]

    if ('迟到' in q or '早退' in q) and ('说明' in q or '提交' in q):
        return {
            "answer": (
                "关于迟到/早退是否需要提交说明：\n\n"
                "根据公司《考勤管理制度》：\n"
                "- **30分钟以内**：扣减当月绩效分1分，一般无需另行提交书面说明\n"
                "- **超过30分钟**：按旷工处理，建议当日通过考勤系统提交考勤异常说明，经直属上级审批\n"
                "- **忘记打卡/漏打卡**：需在当日内提交补卡申请\n\n"
                "如有特殊情况或需 HR 协助，可以说「我想提交考勤异常说明」创建工单。"
            ),
            "source_docs": source_docs,
        }

    if '忘记打卡' in q and ('说明' in q or '提交' in q):
        return {
            "answer": (
                "关于忘记打卡是否需要提交说明：\n\n"
                "根据补卡规则，忘记打卡的员工**需在当日内**通过考勤系统提交补卡申请，"
                "经直属上级审批后生效。每月允许补卡不超过3次。\n\n"
                "如超过补卡次数或情况特殊，可提交「考勤异常说明」工单联系 HR。"
            ),
            "source_docs": [{"source": "考勤制度", "document": "考勤管理制度", "name": "补卡规则"}],
        }

    return {}


# 工龄福利相关关键词
SENIORITY_WELFARE_KEYWORDS = ['工龄福利', '年终奖', '工龄增量', '积累工作']


def _calc_seniority_bonus(work_years: int) -> int:
    """每满3年年终奖额外增加1000元（累计）"""
    if work_years < 3:
        return 0
    return (work_years // 3) * 1000


def is_seniority_welfare_calculation_question(question: str) -> bool:
    """问题是否含工龄年数且询问工龄福利/年终奖"""
    q = (question or "").strip()
    if not _parse_years_expression(q):
        return False
    if any(k in q for k in ('福利', '工龄福利', '年终奖', '司龄', '工龄')):
        return True
    if any(p in q for p in ('积累工作', '累计工作', '工作年限')) and any(
        k in q for k in ('福利', '规定', '有什么', '哪些')
    ):
        return True
    return False


def get_seniority_welfare_followup_answer(resolved_question: str) -> Dict[str, Any]:
    """工龄福利主题工龄追问的直接计算回答（依据 FAQ 每3年+1000元规则）"""
    parsed = _parse_years_expression(resolved_question)
    if not parsed:
        return {}

    years, modifier = parsed
    if modifier == '以上':
        effective_years = years
        years_desc = f"{years}年以上"
    elif modifier in ('以内', '不满'):
        effective_years = years
        years_desc = f"{years}年{modifier}"
    else:
        effective_years = years
        years_desc = f"{years}年"

    bonus = _calc_seniority_bonus(effective_years)
    increments = effective_years // 3
    source_docs = [
        {"source": "福利制度", "document": "工龄福利管理办法", "name": "工龄年终奖增量", "faq_id": 9}
    ]

    if bonus == 0:
        answer = (
            f"结合您之前关于工龄福利的问题，按累计工龄 **{years_desc}** 计算：\n\n"
            "根据公司规定：每工作满3年，年终奖额外增加1000元。\n\n"
            "**您目前工龄不足3年，暂未享受工龄增量年终奖。**\n\n"
            "温馨提示：工龄福利随累计司龄递增，每满3年增加1000元。"
        )
    else:
        answer = (
            f"结合您之前关于工龄福利的问题，按累计工龄 **{years_desc}** 计算：\n\n"
            "根据公司规定：\n"
            "- 每工作满3年，年终奖额外增加1000元\n"
            "- 增量按累计司龄计算，可叠加\n\n"
            f"**您已累计工作 {effective_years} 年，对应 {increments} 个3年周期，"
            f"年终奖金额外增加 {bonus} 元。**\n\n"
            "温馨提示：具体发放以 HR 核定为准。"
        )

    return {"answer": answer, "source_docs": source_docs}


def get_annual_leave_followup_answer(resolved_question: str) -> Dict[str, Any]:
    """年假主题工龄追问的直接回答（依据公司年假制度）"""
    parsed = _parse_years_expression(resolved_question)
    if not parsed:
        return {}

    years, modifier = parsed
    if modifier == '以上':
        effective_years = years
        years_desc = f"{years}年以上"
    elif modifier in ('以内', '不满'):
        effective_years = max(years - 1, 1) if years > 1 else 0
        years_desc = f"{years}年{modifier}"
    else:
        effective_years = years
        years_desc = f"{years}年"

    annual_leave = _calc_annual_leave_days(effective_years)
    source_docs = [{"source": "年假制度", "document": "休假与年假管理办法", "name": "年假计算标准"}]

    if annual_leave == 0:
        answer = (
            f"根据您提到的工龄（{years_desc}），员工入职满1年后才开始享受带薪年假。\n\n"
            "按照公司年假制度：\n"
            "- 工龄1-10年：5天年假\n"
            "- 工龄10-20年：10天年假\n"
            "- 工龄20年以上：15天年假"
        )
    else:
        answer = (
            f"结合您之前关于年假的问题，按工龄 **{years_desc}** 计算：\n\n"
            "按照公司年假制度：\n"
            "- 工龄1-10年：5天年假\n"
            "- 工龄10-20年：10天年假\n"
            "- 工龄20年以上：15天年假\n\n"
            f"**您目前对应 {annual_leave} 天年假。**\n\n"
            "温馨提示：年假需提前申请，请合理安排。"
        )

    return {"answer": answer, "source_docs": source_docs}


def get_recent_context(user_id: int, conversation_id: str, db: Session, limit: int = 3) -> Dict[str, Any]:
    """获取最近的对话上下文（含多轮主题聚合）"""
    records = db.query(QARecord).filter(
        QARecord.user_id == user_id,
        QARecord.conversation_id == conversation_id
    ).order_by(QARecord.created_at.desc()).limit(limit).all()

    if not records:
        return {
            "last_question": "",
            "last_answer_type": "",
            "last_topic": "",
            "conversation_topic": "",
            "last_subtopic": "",
            "last_answer_summary": "",
            "has_history": False,
        }

    last_record = records[0]
    last_question = last_record.question or ""
    last_answer = last_record.answer or ""
    last_answer_type = last_record.answer_type or ""

    conversation_topic = _infer_conversation_topic(records)
    last_topic = conversation_topic or _infer_topic(last_question, last_answer)
    last_subtopic = _infer_subtopic_from_records(records, conversation_topic or last_topic)
    recent_user_questions = [r.question for r in reversed(records) if r.question]
    explicit_annual_leave_intent = any(
        _user_question_explicit_annual_leave(q) for q in recent_user_questions
    )
    has_recent_year_followup = any(
        _is_work_years_related_followup(q) for q in recent_user_questions
    )

    return {
        "last_question": last_question,
        "last_answer_type": last_answer_type,
        "last_topic": last_topic,
        "conversation_topic": conversation_topic,
        "last_subtopic": last_subtopic,
        "last_answer_summary": last_answer[:200] if last_answer else "",
        "has_history": True,
        "recent_user_questions": recent_user_questions,
        "explicit_annual_leave_intent": explicit_annual_leave_intent,
        "has_recent_year_followup": has_recent_year_followup,
    }


def _infer_conversation_topic(records: List[QARecord]) -> str:
    """从最近多轮记录中推断会话主题，澄清/miss 回答只用用户问题推断"""
    topic = ""
    for record in records:
        if record.answer_type in TICKET_ANSWER_TYPES:
            t = _infer_topic(record.question or "", record.answer or "")
            if t == "certify_ticket":
                return "certify_ticket"
        if record.answer_type in SKIP_TOPIC_ANSWER_TYPES:
            q_topic = _infer_topic(record.question or "", "")
            if q_topic != "general":
                topic = q_topic
                break
            continue
        t = _infer_topic(record.question or "", record.answer or "")
        if t != "general":
            return t
    if not topic:
        for record in records:
            if record.answer_type in SKIP_TOPIC_ANSWER_TYPES:
                continue
            t = _infer_topic(record.question or "", record.answer or "")
            if t != "general":
                return t
    return topic


def _infer_subtopic_from_records(records: List[QARecord], topic: str) -> str:
    """从最近用户问题中提取子话题（如迟到、补卡）"""
    if topic != "attendance":
        return ""
    for record in records:
        sub = _extract_attendance_subtopic(record.question or "")
        if sub:
            return sub
    for record in records:
        sub = _extract_attendance_subtopic(record.answer or "")
        if sub:
            return sub
    combined = " ".join(
        f"{record.question or ''} {record.answer or ''}" for record in records
    )
    return _extract_attendance_subtopic(combined)


def _extract_attendance_subtopic(text: str) -> str:
    """从文本中提取考勤子话题"""
    for kw in ATTENDANCE_SUBTOPICS:
        if kw in text:
            return kw
    return ""


def _infer_topic(question: str, answer: str) -> str:
    """从问题和回答中推断主题"""
    text = (question + " " + answer).lower()

    for kw in ANNUAL_LEAVE_KEYWORDS:
        if kw in text:
            return "annual_leave"

    for kw in LEAVE_KEYWORDS:
        if kw in text:
            return "leave_application"

    for kw in CERTIFY_KEYWORDS:
        if kw in text:
            return "certify_ticket"

    if any(kw in text for kw in ['考勤', '打卡', '迟到', '早退', '加班', '补卡', '旷工']):
        return "attendance"

    if any(kw in text for kw in ['工资', '薪资', '社保', '公积金', '报销']):
        return "salary"

    if any(kw in text for kw in ['工龄福利', '年终奖', '福利', '礼金', '补贴']):
        return "salary_welfare"

    return "general"


def rewrite_followup_question(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """改写追问问题"""
    q = question.strip()
    topic = context.get("conversation_topic") or context.get("last_topic", "")
    last_question = context.get("last_question", "")
    last_subtopic = context.get("last_subtopic", "")

    # 0. 问题本身含明确领域词 → 直接展开（无需上下文）
    standalone = _try_standalone_expand(q)
    if standalone:
        return standalone

    # 0b. 指代追问：优先从上一轮用户问题提取考勤子话题
    if is_vague_pronoun_followup(q) or ('说明' in q and ('提交' in q or '需要' in q)):
        subtopic = (
            _extract_attendance_subtopic(last_question)
            or last_subtopic
        )
        if subtopic and _extract_attendance_subtopic(last_question):
            if '说明' in q or '提交' in q:
                resolved = f"{subtopic}需要提交考勤异常说明吗？"
            else:
                resolved = ATTENDANCE_SUBTOPICS.get(subtopic, f"{subtopic}怎么处理？")
            return {
                "is_followup": True,
                "resolved_question": resolved,
                "inherited_topic": "attendance",
                "context_used": True,
            }
        if is_vague_pronoun_followup(q):
            return {
                "is_followup": True,
                "resolved_question": "",
                "inherited_topic": topic,
                "context_used": bool(topic),
                "need_clarification": True,
                "clarification_message": build_pronoun_followup_clarification(context),
            }

    # 1. 工龄/年数追问：无明确年假意图 → 一律澄清，不计算
    if _is_work_years_related_followup(q):
        parsed = _parse_years_expression(q)
        if topic == "salary_welfare" and parsed:
            years, modifier = parsed
            if modifier == '以上':
                resolved = f"累计工作{years}年以上有什么工龄福利？"
            elif modifier in ('以内', '不满'):
                resolved = f"累计工作{years}年{modifier}有什么工龄福利？"
            else:
                resolved = f"累计工作{years}年有什么工龄福利？"
            return {
                "is_followup": True,
                "resolved_question": resolved,
                "inherited_topic": "salary_welfare",
                "context_used": True,
            }
        if not _has_explicit_annual_leave_intent(context):
            return {
                "is_followup": True,
                "resolved_question": "",
                "inherited_topic": topic or "general",
                "context_used": bool(topic),
                "need_clarification": True,
                "clarification_message": build_year_followup_clarification(q),
            }
        parsed = _parse_years_expression(q)
        if parsed:
            years, modifier = parsed
            return {
                "is_followup": True,
                "resolved_question": _build_annual_leave_years_question(years, modifier),
                "inherited_topic": "annual_leave",
                "context_used": True,
                "explicit_annual_leave_intent": True,
            }

    # 场景1：年假主题（非工龄短追问）
    if topic == "annual_leave":
        if q in ['那呢？', '那呢', '呢？', '呢']:
            return {
                "is_followup": True,
                "resolved_question": "",
                "inherited_topic": topic,
                "context_used": True,
                "need_clarification": True,
                "clarification_message": "你是想问工作几年对应多少天年假吗？请补充工龄，例如「工作满3年呢」。",
            }

    # 场景2：请假主题
    if topic == "leave_application":
        if '一样' in q or '也是' in q:
            leave_types = ['病假', '事假', '婚假', '产假', '丧假', '调休']
            for lt in leave_types:
                if lt in q:
                    return {
                        "is_followup": True,
                        "resolved_question": f"{lt}请假是否也需要提前申请？",
                        "inherited_topic": topic,
                        "context_used": True,
                    }

        if '多久' in q:
            return {
                "is_followup": True,
                "resolved_question": "请假需要提前多久申请？",
                "inherited_topic": topic,
                "context_used": True,
            }

    # 场景3：考勤主题
    if topic == "attendance":
        for keyword, resolved in ATTENDANCE_SUBTOPICS.items():
            if keyword in q:
                return {
                    "is_followup": True,
                    "resolved_question": resolved,
                    "inherited_topic": topic,
                    "context_used": True,
                }

        # 指代追问：「这个需要提交说明吗？」→ 继承最近考勤子话题
        if is_vague_pronoun_followup(q) or ('说明' in q and ('提交' in q or '需要' in q)):
            context_text = last_question + " " + context.get("last_answer_summary", "")
            subtopic = (
                last_subtopic
                or _extract_attendance_subtopic(last_question)
                or _extract_attendance_subtopic(context_text)
            )
            if subtopic:
                if '说明' in q or '提交' in q:
                    resolved = f"{subtopic}需要提交考勤异常说明吗？"
                else:
                    resolved = ATTENDANCE_SUBTOPICS.get(subtopic, f"{subtopic}怎么处理？")
                return {
                    "is_followup": True,
                    "resolved_question": resolved,
                    "inherited_topic": topic,
                    "context_used": True,
                }

        # 「那XX呢？」短追问，尝试从上一轮继承子话题类型
        if q.startswith('那') and '呢' in q and len(q) < 12:
            subtopic = last_subtopic or _extract_attendance_subtopic(last_question)
            if subtopic:
                return {
                    "is_followup": True,
                    "resolved_question": ATTENDANCE_SUBTOPICS.get(subtopic, f"{subtopic}怎么处理？"),
                    "inherited_topic": topic,
                    "context_used": True,
                }

    # 场景4：工龄福利主题 + 含年数
    if topic == "salary_welfare":
        parsed = _parse_years_expression(q)
        if parsed:
            years, modifier = parsed
            if modifier == '以上':
                resolved = f"累计工作{years}年以上有什么工龄福利？"
            elif modifier in ('以内', '不满'):
                resolved = f"累计工作{years}年{modifier}有什么工龄福利？"
            else:
                resolved = f"累计工作{years}年有什么工龄福利？"
            return {
                "is_followup": True,
                "resolved_question": resolved,
                "inherited_topic": "salary_welfare",
                "context_used": True,
            }

    # 场景5：证明/工单主题
    if topic == "certify_ticket":
        from app.services.ticket_flow_service import is_ticket_flow_followup

        if is_ticket_flow_followup(q, "certify"):
            resolved = q
            if "这个" in q or "那个" in q:
                if any(kw in q for kw in ["多久", "几天", "时间", "要等"]):
                    resolved = "在职证明开具需要多久？"
                elif any(kw in q for kw in ["材料", "资料", "准备"]):
                    resolved = "开具在职证明需要准备什么材料？"
                elif any(kw in q for kw in ["通知", "告知", "提醒"]):
                    resolved = "在职证明办理完成后会通知我吗？"
            return {
                "is_followup": True,
                "resolved_question": resolved,
                "inherited_topic": topic,
                "context_used": True,
                "is_ticket_question": True,
            }

        return {
            "is_followup": True,
            "resolved_question": q,
            "inherited_topic": topic,
            "context_used": True,
            "is_ticket_question": True,
        }

    # 无明确主题的可疑短追问 → 澄清
    if topic in ("general", "") and (is_year_number_followup(q) or is_vague_pronoun_followup(q)):
        return {
            "is_followup": True,
            "resolved_question": "",
            "inherited_topic": topic,
            "context_used": False,
            "need_clarification": True,
            "clarification_message": build_no_context_clarification(q),
        }

    return {
        "is_followup": True,
        "resolved_question": q,
        "inherited_topic": topic,
        "context_used": bool(topic),
    }
