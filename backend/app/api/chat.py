import re
import json
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success, error
from app.schemas.qa import ChatRequest, ChatResponse
from app.models.qa import QARecord, FAQ, Rule, QAMiss
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.models.ticket import Ticket
from app.services.rag.vectorstore import search_similar
from app.services.llm import (
    generate_answer,
    analyze_intent,
    generate_clarification,
    generate_knowledge_answer,
    is_ai_service_error,
)
from app.services.text_splitter import extract_keywords
import jieba
from app.services.conversation_state_service import ConversationStateService
from app.services.slot_extractor import extract_slots_for_intent
from app.services.ticket_intent_service import (
    detect_ticket_intent,
    TICKET_SLOT_CONFIG,
    build_ticket_type_selection_answer,
    parse_ticket_type_choice,
    is_generic_new_ticket_intent,
)
from app.services.ticket_slot_extractor import extract_ticket_slots, apply_single_missing_slot_fallback
from app.services.ticket_flow_service import (
    is_ticket_cancel_intent,
    is_ticket_modify_intent,
    is_ticket_confirm_intent,
    is_ticket_validation_intent,
    is_ticket_info_query,
    is_ticket_resume_intent,
    is_general_question_instead_of_ticket,
    is_ticket_flow_followup,
    is_weak_ticket_reply,
    should_extract_slot_updates,
    extract_slot_field_updates,
    build_ticket_modify_prompt,
    build_ticket_slot_clarification,
    build_ticket_validation_answer,
    merge_ticket_slots,
    ticket_exit_to_qa_notice,
    answer_ticket_followup_question,
    TICKET_MODIFY_WORDS,
    is_ticket_control_phrase,
    normalize_ticket_filled,
    ticket_draft_display_fields,
    _is_field_change_intent,
)
from app.services.followup_service import (
    is_followup_question,
    get_recent_context,
    rewrite_followup_question,
    build_no_context_clarification,
    is_unresolved_followup,
    was_followup_rewritten,
    get_attendance_policy_answer,
    get_annual_leave_followup_answer,
    get_seniority_welfare_followup_answer,
    is_seniority_welfare_calculation_question,
    is_ambiguous_followup_without_keywords,
    expand_clarification_choice,
)

router = APIRouter()

TICKET_CLARIFY_ACTIONS = [
    {"type": "manual_fill", "label": "手动填写"},
]

TICKET_CONFIRM_ACTIONS = [
    {"type": "confirm_submit", "label": "确认提交"},
    {"type": "modify", "label": "继续修改"},
    {"type": "manual_fill", "label": "手动填写"},
]

_FOLLOWUP_TOPIC_NAMES = {
    "annual_leave": "年假",
    "leave_application": "请假",
    "attendance": "考勤",
    "salary": "薪酬",
    "salary_welfare": "工龄福利",
    "probation": "试用转正",
}


def _ai_enhance_answer(
    question: str,
    knowledge: str,
    history: str = "",
    source_label: str = "标准答案",
    context_hint: str = "",
    fallback: str = "",
) -> str:
    """将 FAQ/规则/制度知识经 AI 改写为自然回答；失败时回退到 fallback"""
    ai_answer = generate_knowledge_answer(
        question=question,
        knowledge=knowledge,
        history=history,
        source_label=source_label,
        context_hint=context_hint,
    )
    if ai_answer and not is_ai_service_error(ai_answer):
        return ai_answer
    return fallback or knowledge


def _followup_context_hint(followup_context: dict) -> str:
    topic = followup_context.get("inherited_topic", "")
    if not topic:
        return ""
    topic_name = _FOLLOWUP_TOPIC_NAMES.get(topic, "")
    if not topic_name:
        return ""
    return f"用户当前问题是对之前「{topic_name}」相关话题的追问，请结合上下文作答。"


def get_or_create_conversation_id(db: Session, user_id: int, conversation_id: str = None) -> str:
    if conversation_id:
        return conversation_id
    return str(uuid.uuid4())[:16]


def _save_clarification_response(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    answer: str,
    intent: str = "followup_clarification",
) -> dict:
    """保存并返回 clarification 类型回答"""
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": answer,
        "answer_type": "clarification",
        "intent": intent,
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": [],
    })


def _save_policy_response(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    answer: str,
    source_docs: list,
    history: str = "",
    context_hint: str = "",
) -> dict:
    """保存并返回制度政策类 rule 回答（经 AI 润色）"""
    if not history:
        history = get_conversation_context(db, user_id, conv_id)
    enhanced = _ai_enhance_answer(
        question=question,
        knowledge=answer,
        history=history,
        source_label="公司制度规定",
        context_hint=context_hint,
        fallback=answer,
    )
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=enhanced,
        answer_type="rule",
        source_docs=json.dumps(source_docs),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": enhanced,
        "answer_type": "rule",
        "source_docs": source_docs,
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": [],
    })


def _save_faq_response(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    faq: FAQ,
    history: str = "",
    context_hint: str = "",
) -> dict:
    """保存并返回 FAQ 回答（经 AI 润色）"""
    knowledge = f"标准问题：{faq.question}\n标准答案：{faq.answer}"
    fallback = (
        f"根据公司规定，{faq.answer}"
        if faq.answer
        else f"关于「{faq.question}」，请参考公司相关制度。"
    )
    answer = _ai_enhance_answer(
        question=question,
        knowledge=knowledge,
        history=history,
        source_label="标准FAQ",
        context_hint=context_hint,
        fallback=fallback,
    )
    source_docs = [{"faq_id": faq.id, "question": faq.question}]
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="faq",
        source_docs=json.dumps(source_docs),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": answer,
        "answer_type": "faq",
        "source_docs": source_docs,
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": [],
    })


def _save_rule_response(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    rule: Rule,
    history: str = "",
    context_hint: str = "",
) -> dict:
    """保存并返回规则匹配回答（经 AI 润色）"""
    knowledge = f"规则名称：{rule.name}\n规定内容：\n{rule.answer_template}"
    fallback = rule.answer_template or f"请参考公司规则「{rule.name}」。"
    answer = _ai_enhance_answer(
        question=question,
        knowledge=knowledge,
        history=history,
        source_label="公司规则",
        context_hint=context_hint,
        fallback=fallback,
    )
    source_docs = [{"rule_id": rule.id, "name": rule.name}]
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="rule",
        source_docs=json.dumps(source_docs),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": answer,
        "answer_type": "rule",
        "source_docs": source_docs,
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": [],
    })


def _try_attendance_followup_answer(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    resolved_question: str,
    followup_context: dict,
) -> Optional[dict]:
    """考勤主题追问的政策兜底回答"""
    if followup_context.get("inherited_topic") != "attendance":
        return None
    if not was_followup_rewritten(question, followup_context):
        return None
    policy = get_attendance_policy_answer(resolved_question)
    if not policy:
        return None
    return _save_policy_response(
        db, user_id, conv_id, question, policy["answer"], policy.get("source_docs", []),
        context_hint=_followup_context_hint(followup_context),
    )


def _try_seniority_welfare_followup_answer(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    resolved_question: str,
    followup_context: dict,
    conversation_topic: str = "",
) -> Optional[dict]:
    """工龄福利主题含年数追问的直接计算回答"""
    calc_q = resolved_question if _parse_years_for_welfare(resolved_question) else question
    if not is_seniority_welfare_calculation_question(calc_q):
        return None

    if followup_context.get("is_followup"):
        topic = followup_context.get("inherited_topic") or conversation_topic
        if topic and topic not in ("salary_welfare",):
            return None

    policy = get_seniority_welfare_followup_answer(calc_q)
    if not policy:
        return None
    return _save_policy_response(
        db, user_id, conv_id, question, policy["answer"], policy.get("source_docs", []),
        context_hint=_followup_context_hint(followup_context),
    )


def _parse_years_for_welfare(text: str) -> bool:
    from app.services.followup_service import _parse_years_expression
    return _parse_years_expression(text or "") is not None


def _try_annual_leave_followup_answer(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    resolved_question: str,
    followup_context: dict,
) -> Optional[dict]:
    """年假主题工龄追问的直接计算回答（需用户曾明确问过年假）"""
    if not followup_context.get("explicit_annual_leave_intent"):
        return None
    if followup_context.get("inherited_topic") != "annual_leave":
        return None
    if not was_followup_rewritten(question, followup_context):
        return None
    policy = get_annual_leave_followup_answer(resolved_question)
    if not policy:
        return None
    return _save_policy_response(
        db, user_id, conv_id, question, policy["answer"], policy.get("source_docs", []),
        context_hint=_followup_context_hint(followup_context),
    )


def get_conversation_context(db: Session, user_id: int, conversation_id: str, limit: int = 3) -> str:
    """获取对话历史上下文"""
    if not conversation_id:
        return ""
    records = db.query(QARecord).filter(
        QARecord.user_id == user_id,
        QARecord.conversation_id == conversation_id
    ).order_by(QARecord.created_at.desc()).limit(limit).all()
    if not records:
        return ""
    context = "以下是之前的对话记录：\n"
    for r in reversed(records):
        q = r.question[:50] if r.question else ""
        a = r.answer[:100] if r.answer else ""
        context += f"问：{q}\n答：{a}\n\n"
    return context


def is_annual_leave_days_question(question: str) -> bool:
    """
    判断是否是年假天数查询问题

    判断规则：
    1. 包含"年假"
    2. 包含以下任意表达：几天、多少天、有多少、我有多少、今年有几天、能休几天、可以休几天、年假天数
    """
    if "年假" not in question:
        return False

    # 年假天数相关的表达
    days_expressions = [
        "几天", "多少天", "有多少", "我有多少", "今年有几天",
        "能休几天", "可以休几天", "年假天数", "年假有几天",
        "有多少天", "能有几天", "可休几天", "几天年假",
        "多少天年假", "几天假"
    ]

    return any(expr in question for expr in days_expressions)


def handle_annual_leave_clarification(question: str, conv_id: str, user_id: int, db: Session) -> dict:
    """
    处理年假澄清：设置 pending_intent，返回澄清回答
    """
    state_service = ConversationStateService(db)

    # 设置 pending_intent
    state_service.set_pending_intent(
        user_id=user_id,
        conversation_id=conv_id,
        intent="annual_leave_calculation",
        required_slots=["join_date", "work_years"]
    )

    # 生成澄清回答
    answer = "年假天数根据工龄不同而不同，我需要确认您的情况。\n\n"
    answer += "请补充以下任意一项：\n"
    answer += "1. 您的入职日期（如：2020年1月1日）\n"
    answer += "2. 您的累计工作年限（如：5年）\n\n"
    answer += "这样我就能准确告诉您有多少天年假了。"

    # 保存问答记录
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success({
        "answer": answer,
        "answer_type": "clarification",
        "intent": "annual_leave_calculation",
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": ["join_date", "work_years"],
        "filled_slots": {},
        "actions": []
    })


def handle_pending_intent(question: str, state, user_id: int, db: Session) -> dict:
    """
    处理待补充信息的意图

    当存在 pending_intent 时，把用户输入当作补充信息处理
    """
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    if state.pending_intent == "annual_leave_calculation":
        # 提取槽位
        slots = extract_slots_for_intent(question, "annual_leave_calculation")

        if not slots:
            # 无法提取到有效信息，提示用户重新输入
            answer = "抱歉，我没能从您的回复中提取到有效信息。\n\n"
            answer += "请补充以下任意一项：\n"
            answer += "1. 您的入职日期（如：2020年1月1日）\n"
            answer += "2. 您的累计工作年限（如：5年）"

            record = QARecord(
                user_id=user_id,
                question=question,
                answer=answer,
                answer_type="clarification",
                source_docs=json.dumps([]),
                conversation_id=conv_id
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return success({
                "answer": answer,
                "answer_type": "clarification",
                "intent": "annual_leave_calculation",
                "source_docs": [],
                "record_id": record.id,
                "conversation_id": conv_id,
                "required_slots": state_service.get_required_slots(user_id, conv_id),
                "filled_slots": state_service.get_filled_slots(user_id, conv_id),
                "actions": []
            })

        # 更新已填充的槽位
        state_service.update_filled_slots(user_id, conv_id, slots)

        # 检查是否所有槽位都已填充
        if not state_service.check_slots_filled(user_id, conv_id):
            # 还有槽位未填充，继续询问
            filled = state_service.get_filled_slots(user_id, conv_id)
            required = state_service.get_required_slots(user_id, conv_id)
            missing = [s for s in required if s not in filled]

            answer = "感谢您提供的信息。"
            if "join_date" in missing:
                answer += "请再补充您的入职日期。"
            elif "work_years" in missing:
                answer += "请再补充您的累计工作年限。"

            record = QARecord(
                user_id=user_id,
                question=question,
                answer=answer,
                answer_type="clarification",
                source_docs=json.dumps([]),
                conversation_id=conv_id
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return success({
                "answer": answer,
                "answer_type": "clarification",
                "intent": "annual_leave_calculation",
                "source_docs": [],
                "record_id": record.id,
                "conversation_id": conv_id,
                "required_slots": required,
                "filled_slots": filled,
                "actions": []
            })

        # 所有槽位已填充，计算年假
        filled = state_service.get_filled_slots(user_id, conv_id)
        work_years = filled.get("work_years", 0)

        # 计算年假天数
        if work_years < 1:
            annual_leave = 0
            answer = f"根据您提供的信息，您的工龄不足1年，暂不享受带薪年假。\n\n"
            answer += "根据公司制度，员工入职满1年后可享受带薪年假。"
        elif work_years < 10:
            annual_leave = 5
        elif work_years < 20:
            annual_leave = 10
        else:
            annual_leave = 15

        if annual_leave > 0:
            answer = f"根据您提供的信息，您的工龄约为 **{work_years}年**。\n\n"
            answer += "按照公司年假制度：\n"
            answer += "- 工龄1-10年：5天年假\n"
            answer += "- 工龄10-20年：10天年假\n"
            answer += "- 工龄20年以上：15天年假\n\n"
            answer += f"**您目前享有 {annual_leave} 天年假。**\n\n"
            answer += "温馨提示：年假需提前申请，请合理安排。"

        # 清空 pending_intent
        state_service.clear_pending_intent(user_id, conv_id)

        source_docs = [{"source": "年假制度", "document": "休假与年假管理办法"}]
        result = _save_policy_response(
            db, user_id, conv_id, question, answer, source_docs,
            history=get_conversation_context(db, user_id, conv_id),
        )
        result["data"]["intent"] = "annual_leave_calculation"
        result["data"]["filled_slots"] = filled
        return result

    # 未知的 pending_intent，清空并走正常流程
    state_service.clear_pending_intent(user_id, conv_id)
    return None


def _begin_ticket_flow(
    question: str,
    conv_id: str,
    user_id: int,
    db: Session,
    ticket_type: str,
) -> dict:
    """在工单类型已确定后，初始化槽位并返回澄清或确认卡片"""
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
    slots = extract_ticket_slots(question, ticket_type)

    filled_slots = {
        "ticket_type": ticket_type,
        "title": config["title"],
        "display_type": config["display_type"],
    }
    filled_slots.update(slots)
    filled_slots = normalize_ticket_filled(ticket_type, filled_slots)

    state_service = ConversationStateService(db)
    state_service.set_pending_intent(
        user_id=user_id,
        conversation_id=conv_id,
        intent="ticket_create",
        required_slots=config["required_slots"],
    )
    state_service.update_filled_slots(user_id, conv_id, filled_slots)

    if state_service.check_slots_filled(user_id, conv_id):
        return _build_ticket_confirm(question, conv_id, user_id, db, ticket_type, state_service)

    missing_slots = [s for s in config["required_slots"] if s not in filled_slots]
    answer = f"好的，我来帮您提交「{config['display_type']}」申请。\n\n"
    if missing_slots:
        answer += "还需要补充以下信息：\n"
        for i, slot in enumerate(missing_slots, 1):
            label = config["slot_labels"].get(slot, slot)
            answer += f"{i}. {label}\n"
        if config.get("display_type") == "证明开具":
            answer += (
                "\n示例：「用来办签证，交给日本领事馆，要盖章，最好这周五前完成」\n"
                "如想先问其它问题，可直接提问；回复「取消」可放弃本次申请。"
            )
        elif config.get("display_type") == "考勤异常":
            answer += (
                "\n示例：「2026年7月3日, 打卡缺失, 忘记打卡」\n"
                "（日期、异常类型、原因 — AI 会自动整理）\n"
                "也可点击下方「手动填写」按钮；回复「取消」可放弃本次申请。"
            )
        else:
            answer += "\n如想先问其它问题，可直接提问；也可点击「手动填写」按钮；回复「取消」可放弃本次申请。"

    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success({
        "answer": answer,
        "answer_type": "ticket_clarification",
        "intent": "ticket_create",
        "ticket_type": ticket_type,
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": config["required_slots"],
        "filled_slots": filled_slots,
        "slot_labels": config["slot_labels"],
        "actions": TICKET_CLARIFY_ACTIONS,
    })


def _start_ticket_type_selection(
    question: str,
    conv_id: str,
    user_id: int,
    db: Session,
) -> dict:
    """用户要新建工单但未指明类型，引导选择"""
    state_service = ConversationStateService(db)
    state_service.set_pending_intent(
        user_id=user_id,
        conversation_id=conv_id,
        intent="ticket_type_select",
        required_slots=[],
    )
    answer = build_ticket_type_selection_answer()
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": answer,
        "answer_type": "ticket_clarification",
        "intent": "ticket_type_select",
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": [],
    })


def handle_ticket_type_select(question: str, state, user_id: int, db: Session) -> Optional[dict]:
    """处理工单类型选择"""
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    if is_ticket_cancel_intent(question):
        state_service.clear_pending_intent(user_id, conv_id)
        answer = "好的，已取消本次工单申请。如需办理，您可以随时重新发起。"
        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="ticket_clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "ticket_clarification",
            "intent": "ticket_create",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": [],
        })

    ticket_type = parse_ticket_type_choice(question)
    if not ticket_type:
        answer = build_ticket_type_selection_answer()
        answer = "抱歉，我没能识别您要申请的工单类型。\n\n" + answer
        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="ticket_clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "ticket_clarification",
            "intent": "ticket_type_select",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": [],
        })

    state_service.clear_pending_intent(user_id, conv_id)
    return _begin_ticket_flow(question, conv_id, user_id, db, ticket_type)


def handle_ticket_create(question: str, conv_id: str, user_id: int, db: Session) -> dict:
    """
    处理工单创建：识别工单意图，设置 pending_intent，返回澄清
    """
    intent_result = detect_ticket_intent(question)

    if not intent_result["is_ticket_intent"]:
        return None

    if intent_result.get("needs_type_selection"):
        return _start_ticket_type_selection(question, conv_id, user_id, db)

    ticket_type = intent_result["ticket_type"]
    return _begin_ticket_flow(question, conv_id, user_id, db, ticket_type)


_ticket_exit_notice: str = ""


def _set_ticket_exit_notice(notice: str) -> None:
    global _ticket_exit_notice
    _ticket_exit_notice = notice


def _consume_ticket_exit_notice() -> str:
    global _ticket_exit_notice
    notice = _ticket_exit_notice
    _ticket_exit_notice = ""
    return notice


def _prepend_ticket_notice(response: dict, notice: str) -> dict:
    if not notice or not response:
        return response
    data = response.get("data")
    if isinstance(data, dict) and data.get("answer"):
        data = dict(data)
        data["answer"] = f"{notice}\n\n{data['answer']}"
        return {**response, "data": data}
    return response


def _collect_ticket_slot_updates(
    question: str,
    ticket_type: str,
    config: dict,
    filled: dict,
) -> dict:
    """提取槽位并在一项缺失时用用户原话兜底"""
    if is_ticket_control_phrase(question):
        return {}
    if is_ticket_confirm_intent(question, None) or is_ticket_modify_intent(question, None):
        return {}

    # 字段修改（如「异常原因改成忘记」）优先走专用解析，避免误匹配
    if _is_field_change_intent(question) or should_extract_slot_updates(question):
        updates = extract_slot_field_updates(question, ticket_type, filled=filled)
        if updates:
            return apply_single_missing_slot_fallback(
                question, ticket_type, config, filled, updates
            )

    slots = extract_ticket_slots(question, ticket_type, filled=filled)
    return apply_single_missing_slot_fallback(question, ticket_type, config, filled, slots)


def _ticket_draft_fields(config: dict, filled: dict) -> dict:
    """确认卡片仅展示必填槽位"""
    return ticket_draft_display_fields(config, filled)


def handle_manual_ticket_fill(
    question: str,
    state,
    user_id: int,
    db: Session,
    ticket_slots: dict,
) -> Optional[dict]:
    """处理手动填写工单槽位"""
    if not ticket_slots:
        return None

    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    try:
        filled = json.loads(state.filled_slots) if state.filled_slots else {}
    except Exception:
        filled = {}

    ticket_type = filled.get("ticket_type")
    if not ticket_type:
        return None

    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
    cleaned = {
        k: v for k, v in ticket_slots.items()
        if k in config["required_slots"] and v not in (None, "")
    }
    if ticket_type == "attendance_exception" and cleaned.get("reason"):
        cleaned["description"] = cleaned["reason"]

    for key, val in cleaned.items():
        filled[key] = val
    filled = normalize_ticket_filled(ticket_type, filled)
    state_service.update_filled_slots(user_id, conv_id, filled)

    if state_service.check_slots_filled(user_id, conv_id):
        return _build_ticket_confirm("已手动填写工单", conv_id, user_id, db, ticket_type, state_service)

    missing = [s for s in config["required_slots"] if s not in filled]
    answer = build_ticket_slot_clarification(
        config, missing, hint="手动填写后仍有必填项未完整，请继续补充："
    )
    return _save_ticket_clarification(db, user_id, conv_id, question or "手动填写工单", answer, ticket_type, config, filled)


def handle_ticket_pending(question: str, state, user_id: int, db: Session, action: str = None) -> Optional[dict]:
    """
    处理工单槽位补充
    返回 None 表示已退出工单流程，应继续正常问答
    """
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    try:
        filled = json.loads(state.filled_slots) if state.filled_slots else {}
    except Exception:
        filled = {}

    ticket_type = filled.get("ticket_type", "other")
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    if is_ticket_cancel_intent(question):
        state_service.clear_pending_intent(user_id, conv_id)
        answer = "好的，已取消本次工单申请。如需办理，您可以随时重新发起。"
        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="ticket_clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "ticket_clarification",
            "intent": "ticket_create",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": [],
        })

    if is_general_question_instead_of_ticket(question, ticket_type):
        state_service.pause_ticket_for_qa(user_id, conv_id)
        _set_ticket_exit_notice(ticket_exit_to_qa_notice(ticket_type))
        return None

    if is_ticket_confirm_intent(question, action):
        if state_service.check_slots_filled(user_id, conv_id):
            return handle_ticket_confirm(question, state, user_id, db, action)
        missing = [s for s in config["required_slots"] if s not in filled]
        answer = build_ticket_slot_clarification(
            config, missing, hint="信息尚未填写完整，暂时无法提交。"
        )
        return _save_ticket_clarification(db, user_id, conv_id, question, answer, ticket_type, config, filled)

    if is_ticket_control_phrase(question):
        answer = (
            "请点击消息下方的「手动填写」按钮打开表单填写；"
            "信息无误后请点击「确认提交」。回复「取消」可放弃申请。"
        )
        return _save_ticket_clarification(db, user_id, conv_id, question, answer, ticket_type, config, filled)

    slots = _collect_ticket_slot_updates(question, ticket_type, config, filled)
    if not slots:
        if is_weak_ticket_reply(question, {}):
            missing_slots = [s for s in config["required_slots"] if s not in filled]
            answer = build_ticket_slot_clarification(config, missing_slots)
            return _save_ticket_clarification(db, user_id, conv_id, question, answer, ticket_type, config, filled)
        return _save_ticket_clarification(
            db, user_id, conv_id, question,
            "未能从您的回复中识别到有效信息。请补充工单字段，或点击「手动填写」按钮。",
            ticket_type, config, filled,
        )

    filled = merge_ticket_slots(filled, slots)
    filled = normalize_ticket_filled(ticket_type, filled)
    state_service.update_filled_slots(user_id, conv_id, filled)

    if state_service.check_slots_filled(user_id, conv_id):
        return _build_ticket_confirm(question, conv_id, user_id, db, ticket_type, state_service)

    missing_slots = [s for s in config["required_slots"] if s not in filled]
    if is_weak_ticket_reply(question, slots):
        answer = build_ticket_slot_clarification(config, missing_slots)
        return _save_ticket_clarification(db, user_id, conv_id, question, answer, ticket_type, config, filled)

    answer = "还需要补充以下信息：\n"
    for i, slot in enumerate(missing_slots, 1):
        label = config["slot_labels"].get(slot, slot)
        answer += f"{i}. {label}\n"
    answer += "\n如想先咨询其它问题，可直接提问；回复「取消」可放弃本次申请。"
    return _save_ticket_clarification(db, user_id, conv_id, question, answer, ticket_type, config, filled)


def _save_ticket_clarification(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    answer: str,
    ticket_type: str,
    config: dict,
    filled: dict,
) -> dict:
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return success({
        "answer": answer,
        "answer_type": "ticket_clarification",
        "intent": "ticket_create",
        "ticket_type": ticket_type,
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": config["required_slots"],
        "filled_slots": filled,
        "slot_labels": config["slot_labels"],
        "actions": TICKET_CLARIFY_ACTIONS,
    })


def handle_paused_ticket(
    question: str, state, user_id: int, db: Session, action: str = None
) -> Optional[dict]:
    """处理已暂停的工单：恢复修改/确认，或继续回答其它问题"""
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id
    filled = state_service.get_filled_slots(user_id, conv_id)
    ticket_type = filled.get("ticket_type", "other")
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    if is_ticket_cancel_intent(question):
        state_service.clear_pending_intent(user_id, conv_id)
        answer = "好的，已取消本次工单申请。如需办理，您可以随时重新发起。"
        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="ticket_clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "ticket_clarification",
            "intent": "ticket_create",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": [],
        })

    if is_ticket_resume_intent(question, action):
        if is_ticket_confirm_intent(question, action):
            state_service.resume_ticket(user_id, conv_id, "waiting_for_confirm")
            state = state_service.get_or_create_state(user_id, conv_id)
            return handle_ticket_confirm(question, state, user_id, db, action)

        state_service.resume_ticket(user_id, conv_id, "waiting_for_slot")
        if is_ticket_modify_intent(question, action):
            answer = build_ticket_modify_prompt(config, filled)
            return _save_ticket_clarification(
                db, user_id, conv_id, question, answer, ticket_type, config, filled
            )
        if state_service.check_slots_filled(user_id, conv_id):
            return _build_ticket_confirm(
                question, conv_id, user_id, db, ticket_type, state_service
            )
        answer = build_ticket_modify_prompt(config, filled)
        return _save_ticket_clarification(
            db, user_id, conv_id, question, answer, ticket_type, config, filled
        )

    if should_extract_slot_updates(question):
        slots = _collect_ticket_slot_updates(question, ticket_type, config, filled)
        filled = merge_ticket_slots(filled, slots)
        state_service.update_filled_slots(user_id, conv_id, filled)
        state_service.resume_ticket(user_id, conv_id, "waiting_for_confirm")
        if state_service.check_slots_filled(user_id, conv_id):
            return _build_ticket_confirm(
                question, conv_id, user_id, db, ticket_type, state_service
            )
        missing = [s for s in config["required_slots"] if s not in filled]
        answer = build_ticket_slot_clarification(config, missing)
        return _save_ticket_clarification(
            db, user_id, conv_id, question, answer, ticket_type, config, filled
        )

    if is_ticket_flow_followup(question, ticket_type):
        answer = _answer_ticket_followup_with_lookup(
            db, user_id, conv_id, question, ticket_type, config, filled,
            {"last_answer_type": "ticket_qa"},
        )
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled,
            submitted=bool(_lookup_conversation_ticket(db, user_id, conv_id)),
        )

    if is_ticket_validation_intent(question):
        state_service.resume_ticket(user_id, conv_id, "waiting_for_confirm")
        answer = build_ticket_validation_answer(config, filled)
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled
        )

    if is_ticket_info_query(question):
        answer = _answer_ticket_followup_with_lookup(
            db, user_id, conv_id, question, ticket_type, config, filled,
            {"last_answer_type": "ticket_qa"},
        )
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled,
            submitted=bool(_lookup_conversation_ticket(db, user_id, conv_id)),
        )

    if is_general_question_instead_of_ticket(question, ticket_type):
        return None

    return None


def _build_ticket_confirm(question: str, conv_id: str, user_id: int, db: Session, ticket_type: str, state_service: ConversationStateService) -> dict:
    """构建工单确认卡片"""
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
    filled = normalize_ticket_filled(ticket_type, state_service.get_filled_slots(user_id, conv_id))
    state_service.update_filled_slots(user_id, conv_id, filled)

    display_fields = ticket_draft_display_fields(config, filled)

    # 确认文案与卡片字段完全一致（仅 3 项必填 + 工单类型）
    answer = "请确认以下工单信息：\n\n"
    answer += f"**工单类型：** {config['display_type']}\n"
    for slot, value in display_fields.items():
        label = config["slot_labels"].get(slot, slot)
        if slot == "need_stamp":
            value = "是" if value else "否"
        answer += f"**{label}：** {value}\n"
    answer += "\n确认提交给 HR 吗？"

    # 更新状态为 waiting_for_confirm
    state_service.update_last_answer_type(user_id, conv_id, "ticket_confirm")
    state = state_service.get_or_create_state(user_id, conv_id)
    state.status = "waiting_for_confirm"
    db.commit()

    # 保存问答记录
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_confirm",
        source_docs=json.dumps([]),
        conversation_id=conv_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success({
        "answer": answer,
        "answer_type": "ticket_confirm",
        "intent": "ticket_create",
        "ticket_type": ticket_type,
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": filled,
        "ticket_draft": {
            "type": ticket_type,
            "title": config["display_type"],
            "description": "",
            "fields": display_fields,
        },
        "display_type": config["display_type"],
        "slot_labels": config["slot_labels"],
        "show_confirm_card": True,
        "actions": TICKET_CONFIRM_ACTIONS,
    })


def _lookup_conversation_ticket(db: Session, user_id: int, conv_id: str) -> Optional[Ticket]:
    """查询当前会话中该用户最近提交的真实工单"""
    if not conv_id:
        return None
    return (
        db.query(Ticket)
        .filter(Ticket.creator_id == user_id, Ticket.conversation_id == conv_id)
        .order_by(Ticket.created_at.desc())
        .first()
    )


def _ticket_context_active(state, recent_context: dict) -> bool:
    if state and state.pending_intent == "ticket_create":
        return True
    topic = recent_context.get("conversation_topic") or recent_context.get("last_topic", "")
    if topic == "certify_ticket":
        return True
    if recent_context.get("last_answer_type") in ("ticket_confirm", "ticket_qa", "ticket_submitted", "ticket_clarification"):
        return True
    return False


def _answer_ticket_followup_with_lookup(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    ticket_type: str,
    config: dict,
    filled: dict,
    recent_context: dict,
) -> str:
    ticket_record = _lookup_conversation_ticket(db, user_id, conv_id)
    submitted = bool(ticket_record) or recent_context.get("last_answer_type") == "ticket_submitted"
    return answer_ticket_followup_question(
        question,
        ticket_type,
        config,
        filled,
        submitted=submitted,
        ticket_record=ticket_record,
    )


def _save_ticket_followup_response(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    answer: str,
    ticket_type: str,
    filled: dict,
    *,
    submitted: bool = False,
) -> dict:
    """保存工单上下文追问的回答（展示文字回复，非确认卡片）"""
    answer_type = "ticket_submitted" if submitted else "ticket_qa"
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type=answer_type,
        source_docs=json.dumps([]),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    payload = {
        "answer": answer,
        "answer_type": answer_type,
        "intent": "ticket_create",
        "ticket_type": ticket_type,
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": filled,
        "actions": [],
    }
    if not submitted:
        payload["actions"] = [
            {"type": "confirm_submit", "label": "确认提交"},
            {"type": "modify", "label": "继续修改"},
        ]
    return success(payload)


def _try_ticket_context_answer(
    db: Session,
    user_id: int,
    conv_id: str,
    question: str,
    state,
    recent_context: dict,
    followup_context: dict,
) -> Optional[dict]:
    """
    在工单流程中或刚提交后，回答与工单相关的追问（避免误走 FAQ/RAG/澄清）
    """
    ticket_record = _lookup_conversation_ticket(db, user_id, conv_id)
    in_ticket_context = _ticket_context_active(state, recent_context) or is_ticket_info_query(question)

    if not in_ticket_context:
        return None

    state_service = ConversationStateService(db)
    filled = state_service.get_filled_slots(user_id, conv_id) if state else {}
    ticket_type = filled.get("ticket_type") or "certify"
    if not filled.get("ticket_type"):
        filled = {**filled, "ticket_type": ticket_type}
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    if is_ticket_validation_intent(question) and state and state.pending_intent == "ticket_create":
        answer = build_ticket_validation_answer(config, filled)
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled
        )

    if (
        is_ticket_info_query(question)
        or is_ticket_flow_followup(question, ticket_type)
        or is_ticket_validation_intent(question)
    ):
        answer = _answer_ticket_followup_with_lookup(
            db, user_id, conv_id, question, ticket_type, config, filled, recent_context
        )
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled,
            submitted=bool(ticket_record),
        )

    return None


def _submit_ticket(
    question: str,
    conv_id: str,
    user_id: int,
    db: Session,
    ticket_type: str,
    config: dict,
    filled: dict,
    state_service: ConversationStateService,
) -> dict:
    """正式创建并提交工单"""
    filled = normalize_ticket_filled(ticket_type, filled)

    desc_parts = []
    for slot in config["required_slots"]:
        label = config["slot_labels"].get(slot, slot)
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else "否"
        if value:
            desc_parts.append(f"{label}：{value}")

    description = "\n".join(desc_parts)

    ticket_count = db.query(Ticket).count()
    ticket_no = f"TK{datetime.now().strftime('%Y%m%d')}{ticket_count + 1:04d}"

    ticket = Ticket(
        ticket_no=ticket_no,
        type=ticket_type,
        title=config["title"],
        description=description,
        status="pending",
        creator_id=user_id,
        conversation_id=conv_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    state_service.clear_pending_intent(user_id, conv_id)

    answer = f"已提交人工请求，工单编号：**{ticket_no}**。\n\n"
    answer += "你可以在「我的 - 人工请求」中查看处理进度。"

    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_submitted",
        source_docs=json.dumps([]),
        conversation_id=conv_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success({
        "answer": answer,
        "answer_type": "ticket_submitted",
        "intent": "ticket_create",
        "ticket_type": ticket_type,
        "source_docs": [],
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "ticket": {
            "ticket_id": ticket.id,
            "ticket_no": ticket_no,
            "status": "pending",
        },
        "actions": [],
    })


def handle_ticket_confirm(question: str, state, user_id: int, db: Session, action: str = None) -> Optional[dict]:
    """
    处理工单确认提交
    返回 None 表示已退出工单流程，应继续正常问答
    """
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    try:
        filled = json.loads(state.filled_slots) if state.filled_slots else {}
    except Exception:
        filled = {}

    ticket_type = filled.get("ticket_type", "other")
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    if is_ticket_cancel_intent(question):
        state_service.clear_pending_intent(user_id, conv_id)
        answer = "好的，已取消本次工单申请。如需办理，您可以随时重新发起。"
        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="ticket_clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "ticket_clarification",
            "intent": "ticket_create",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": [],
        })

    if is_ticket_modify_intent(question, action):
        state_service.set_ticket_modify_mode(user_id, conv_id)
        answer = build_ticket_modify_prompt(config, filled)
        return _save_ticket_clarification(
            db, user_id, conv_id, question, answer, ticket_type, config, filled
        )

    if is_ticket_validation_intent(question):
        answer = build_ticket_validation_answer(config, filled)
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled
        )

    if is_ticket_info_query(question):
        answer = _answer_ticket_followup_with_lookup(
            db, user_id, conv_id, question, ticket_type, config, filled,
            {"last_answer_type": "ticket_confirm"},
        )
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled,
            submitted=bool(_lookup_conversation_ticket(db, user_id, conv_id)),
        )

    if is_ticket_confirm_intent(question, action):
        return _submit_ticket(
            question, conv_id, user_id, db, ticket_type, config, filled, state_service
        )

    if is_ticket_control_phrase(question):
        answer = (
            "请点击下方「确认提交」按钮完成提交，或点击「继续修改」/「手动填写」调整信息。"
            "回复「取消」可放弃本次申请。"
        )
        return _save_ticket_followup_response(
            db, user_id, conv_id, question, answer, ticket_type, filled
        )

    if is_general_question_instead_of_ticket(question, ticket_type):
        state_service.pause_ticket_for_qa(user_id, conv_id)
        _set_ticket_exit_notice(ticket_exit_to_qa_notice(ticket_type))
        return None

    slots = _collect_ticket_slot_updates(question, ticket_type, config, filled)
    if slots:
        filled = merge_ticket_slots(filled, slots)
        filled = normalize_ticket_filled(ticket_type, filled)
        state_service.update_filled_slots(user_id, conv_id, filled)
        if state_service.check_slots_filled(user_id, conv_id):
            return _build_ticket_confirm(question, conv_id, user_id, db, ticket_type, state_service)
        missing = [s for s in config["required_slots"] if s not in filled]
        answer = build_ticket_slot_clarification(config, missing)
        return _save_ticket_clarification(db, user_id, conv_id, question, answer, ticket_type, config, filled)

    return _save_ticket_followup_response(
        db, user_id, conv_id, question,
        _answer_ticket_followup_with_lookup(
            db, user_id, conv_id, question, ticket_type, config, filled,
            {"last_answer_type": "ticket_confirm"},
        ),
        ticket_type, filled,
    )


def match_faq(db: Session, question: str, conversation_topic: str = ""):
    """关键词匹配FAQ，不调用API"""
    keywords = extract_keywords(question)
    faqs = db.query(FAQ).filter(FAQ.status == 1).all()

    common_words = {'如何', '怎么', '什么', '为什么', '请', '帮我', '告诉', '一下',
                    '一些', '这个', '那个', '可以', '能否', '是否', '有没有', '想',
                    '知道', '了解', '咨询', '询问', '问', '答', '回答', '问题',
                    '这样', '现在', '公司', '规定', '有没有', '积累'}

    best_match = None
    best_score = 0
    best_matched = []

    q_lower = question.lower()
    user_kw_set = set(keywords)

    for faq in faqs:
        score = 0
        matched = []

        if faq.question and (faq.question.lower() in q_lower or q_lower in faq.question.lower()):
            score += 10

        faq_q_words = {w for w in jieba.lcut(faq.question or "") if len(w) >= 2}
        faq_kw_set = set()
        if faq.keywords:
            faq_kw_set = {k.strip() for k in faq.keywords.split(",") if k.strip()}

        faq_text = (faq.question or "") + "," + (faq.keywords or "")

        for kw in keywords:
            if not kw or kw in common_words:
                continue

            if kw in faq_kw_set:
                score += 4
                matched.append(kw)
            elif kw in faq_q_words:
                score += 3
                matched.append(kw)
            elif len(kw) >= 3 and kw in (faq.question or ""):
                score += 2
                matched.append(kw)

        # 会话主题一致加分
        if conversation_topic == "salary_welfare":
            if any(k in faq_text for k in ("福利", "工龄", "年终奖")):
                score += 5
            if any(k in faq_text for k in ("文档", "AI", "查重")):
                score -= 8

        if conversation_topic == "annual_leave":
            if any(k in faq_text for k in ("年假", "工龄", "休假")):
                score += 5

        # 用户问福利/工龄，惩罚无关 FAQ（如工作文档）
        if any(k in user_kw_set for k in ("福利", "工龄")) or "福利" in question:
            if any(k in faq_text for k in ("福利", "工龄", "年终奖")):
                score += 3
            elif any(k in faq_text for k in ("文档", "AI", "查重", "写作")):
                score -= 10

        if score > best_score:
            best_score = score
            best_match = faq
            best_matched = matched

    if best_match and best_score >= 3:
        all_common = all(kw in common_words for kw in best_matched if kw)
        if all_common and best_score < 6:
            return None

        best_match.view_count += 1
        return best_match
    return None


def match_rule(db: Session, question: str):
    """关键词匹配规则，不调用API"""
    keywords = extract_keywords(question)
    rules = db.query(Rule).filter(Rule.status == 1).order_by(Rule.priority.desc()).all()

    for rule in rules:
        if not rule.trigger_keywords:
            continue
        triggers = [t.strip() for t in rule.trigger_keywords.split(",") if t.strip()]

        for trigger in triggers:
            if trigger and trigger in question:
                return rule

        for kw in keywords:
            if not kw:
                continue
            for trigger in triggers:
                if trigger and (kw in trigger or trigger in kw):
                    return rule
    return None


def rag_search_and_generate(
    question: str,
    history: str = "",
    skip_intent_clarification: bool = False,
    context_hint: str = "",
) -> tuple:
    """RAG搜索 + AI生成回答"""

    intent_result = analyze_intent(question, context_hint=context_hint)

    if not skip_intent_clarification and intent_result.get("need_clarification", False):
        clarification_reason = intent_result.get("clarification_reason", "")
        clarification_hint = intent_result.get("clarification_hint", "请补充更多细节")
        intent = intent_result.get("intent", "其他")

        clarification = f"我注意到您的问题可能需要补充一些信息。\n\n"
        clarification += f"**问题分析：** {clarification_reason}\n\n"
        clarification += f"**建议：** {clarification_hint}\n\n"

        if intent == "考勤":
            clarification += "例如：您可以问「请假需要提前多久申请？」或「加班可以调休吗？」"
        elif intent == "休假":
            clarification += "例如：您可以问「年假有几天？」或「病假需要什么证明？」"
        elif intent == "薪酬":
            clarification += "例如：您可以问「工资是怎么构成的？」或「社保缴纳比例是多少？」"
        elif intent == "绩效":
            clarification += "例如：您可以问「绩效考核标准是什么？」或「绩效申诉怎么提交？」"
        else:
            clarification += "例如：您可以问「试用期多久？」或「报销流程是什么？」"

        return clarification, [], "need_clarification"

    search_results = search_similar(question, top_k=5)

    if not search_results or search_results[0]["score"] < 0.3:
        return None, [], "low_confidence"

    context_parts = []
    sources = []
    for r in search_results[:3]:
        content = r["content"][:300]
        context_parts.append(content)
        meta = r.get("metadata", {})
        sources.append({
            "doc_id": meta.get("doc_id"),
            "chunk": content[:100],
            "score": round(r["score"], 3)
        })

    context = "\n\n".join(context_parts)

    answer = generate_answer(question, context, history)

    miss_keywords = ["未找到", "无法回答", "没有找到", "未查询到", "没有相关信息", "暂未找到"]
    is_miss = any(kw in answer for kw in miss_keywords)

    if is_miss:
        return answer, sources, "low_confidence"

    return answer, sources, "high_confidence"


@router.post("")
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    智能问答主接口

    执行顺序：
    1. 获取/创建 conversation_state
    2. 优先检查 pending_intent（如果有，走补充信息流程）
    3. 判断是否需要年假澄清
    4. 走原有 FAQ/规则/RAG/miss 逻辑
    """
    # Step 1: 获取/创建 conversation_id 和 state
    conv_id = get_or_create_conversation_id(db, current_user.id, data.conversation_id)
    question = data.question.strip()

    if not question:
        return error("请输入问题")

    # Step 2: 获取会话状态
    state_service = ConversationStateService(db)
    state = state_service.get_or_create_state(current_user.id, conv_id)

    # Step 3: 对话轮次 +1
    state_service.increment_turn_count(current_user.id, conv_id)

    paused_notice = ""

    # Step 4: 【第一优先级】检查 pending_intent
    if state.pending_intent:
        if data.action == "manual_fill":
            if data.ticket_slots:
                result = handle_manual_ticket_fill(
                    question, state, current_user.id, db, data.ticket_slots
                )
                if result is not None:
                    return result
            filled_now = state_service.get_filled_slots(current_user.id, conv_id)
            ticket_type = filled_now.get("ticket_type", "other")
            config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
            return _save_ticket_clarification(
                db, current_user.id, conv_id, question,
                "请通过「手动填写」按钮打开表单填写工单信息。",
                ticket_type, config, filled_now,
            )

        # 工单类型选择
        if state.pending_intent == "ticket_type_select":
            result = handle_ticket_type_select(question, state, current_user.id, db)
            if result is not None:
                return result

        # 工单已暂停（用户曾转而提问其它 HR 问题）
        elif state.pending_intent == "ticket_create" and state.status == "ticket_paused":
            result = handle_paused_ticket(question, state, current_user.id, db, data.action)
            if result is not None:
                return result
            state = state_service.get_or_create_state(current_user.id, conv_id)

        # 工单待确认状态
        elif state.pending_intent == "ticket_create" and state.status == "waiting_for_confirm":
            result = handle_ticket_confirm(question, state, current_user.id, db, data.action)
            if result is not None:
                return result
            state = state_service.get_or_create_state(current_user.id, conv_id)
            paused_notice = _consume_ticket_exit_notice()

        # 工单槽位补充状态
        elif state.pending_intent == "ticket_create":
            result = handle_ticket_pending(question, state, current_user.id, db, data.action)
            if result is not None:
                return result
            state = state_service.get_or_create_state(current_user.id, conv_id)
            paused_notice = _consume_ticket_exit_notice()

        # 年假补充信息状态
        elif state.pending_intent == "annual_leave_calculation":
            result = handle_pending_intent(question, state, current_user.id, db)
            if result:
                return result

        else:
            # 其他未知的 pending_intent，清空并走正常流程
            state_service.clear_pending_intent(current_user.id, conv_id)
            state = state_service.get_or_create_state(current_user.id, conv_id)

    def _attach_paused_notice(response: dict) -> dict:
        nonlocal paused_notice
        if paused_notice and response:
            response = _prepend_ticket_notice(response, paused_notice)
            paused_notice = ""
        return response

    # Step 5: 【新增】上下文追问处理
    resolved_question = question
    is_followup = False
    followup_context = {}
    recent_context = get_recent_context(current_user.id, conv_id, db)

    # 工单语境下的校验/查编号问题不走追问澄清
    if _ticket_context_active(state, recent_context) and (
        is_ticket_validation_intent(question) or is_ticket_info_query(question)
    ):
        ticket_ctx_result = _try_ticket_context_answer(
            db, current_user.id, conv_id, question, state, recent_context, {}
        )
        if ticket_ctx_result:
            return _attach_paused_notice(ticket_ctx_result)

    # 用户回复澄清选项（如「工龄福利」）
    choice_result = expand_clarification_choice(question, recent_context)
    if choice_result.get("resolved_question"):
        is_followup = True
        followup_context = choice_result
        resolved_question = choice_result["resolved_question"]

        welfare_result = _try_seniority_welfare_followup_answer(
            db, current_user.id, conv_id, question, resolved_question, followup_context,
            conversation_topic=recent_context.get("conversation_topic", ""),
        )
        if welfare_result:
            return welfare_result

    if is_followup_question(question) and not choice_result.get("resolved_question"):
        has_history = recent_context.get("has_history", False)

        followup_result = rewrite_followup_question(question, recent_context)
        if followup_result.get("is_followup"):
            is_followup = True
            followup_context = followup_result

            if followup_result.get("need_clarification"):
                answer = followup_result.get("clarification_message", build_no_context_clarification(question))
                return _save_clarification_response(
                    db, current_user.id, conv_id, question, answer, "followup_clarification"
                )

            if followup_result.get("resolved_question"):
                resolved_question = followup_result["resolved_question"]

            policy_result = _try_attendance_followup_answer(
                db, current_user.id, conv_id, question, resolved_question, followup_context
            )
            if policy_result:
                return policy_result

            annual_result = _try_annual_leave_followup_answer(
                db, current_user.id, conv_id, question, resolved_question, followup_context
            )
            if annual_result:
                return annual_result

            welfare_result = _try_seniority_welfare_followup_answer(
                db, current_user.id, conv_id, question, resolved_question, followup_context,
                conversation_topic=recent_context.get("conversation_topic", ""),
            )
            if welfare_result:
                return welfare_result

            # 无历史 + 无法展开 + 真正模糊 → 澄清
            if not has_history and not was_followup_rewritten(question, followup_context):
                if is_ambiguous_followup_without_keywords(question):
                    answer = build_no_context_clarification(question)
                    return _save_clarification_response(
                        db, current_user.id, conv_id, question, answer, "followup_no_context"
                    )
        elif not has_history and is_ambiguous_followup_without_keywords(question):
            answer = build_no_context_clarification(question)
            return _save_clarification_response(
                db, current_user.id, conv_id, question, answer, "followup_no_context"
            )

    # Step 6: 【第二优先级】判断是否是工单意图
    ticket_result = handle_ticket_create(question, conv_id, current_user.id, db)
    if ticket_result:
        return ticket_result

    # 工单上下文追问（确认前/暂停中/刚提交后）
    ticket_ctx_result = _try_ticket_context_answer(
        db, current_user.id, conv_id, question, state, recent_context, followup_context
    )
    if ticket_ctx_result:
        return _attach_paused_notice(ticket_ctx_result)

    # 证明办理语境：优先处理校验/提交/查编号，避免误匹配 FAQ
    conversation_topic_early = recent_context.get("conversation_topic") or recent_context.get("last_topic", "")
    if _ticket_context_active(state, recent_context):
        if is_ticket_validation_intent(question) and state.pending_intent == "ticket_create":
            filled = state_service.get_filled_slots(current_user.id, conv_id)
            ticket_type = filled.get("ticket_type", "certify")
            config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
            return _save_ticket_followup_response(
                db, current_user.id, conv_id, question,
                build_ticket_validation_answer(config, filled),
                ticket_type, filled,
            )
        if (
            conversation_topic_early == "certify_ticket"
            and state.pending_intent == "ticket_create"
            and is_ticket_confirm_intent(question, data.action)
        ):
            if state.status == "ticket_paused":
                state_service.resume_ticket(current_user.id, conv_id, "waiting_for_confirm")
                state = state_service.get_or_create_state(current_user.id, conv_id)
            return handle_ticket_confirm(question, state, current_user.id, db, data.action)

    # Step 6: 【第三优先级】判断是否是公告意图（公告发布走HR后台，不在聊天中处理）
    notice_keywords = ['发布公告', '发通知', '发布通知', '发公告', '通知公告', '通知大家', '通知全体员工']
    if any(kw in question for kw in notice_keywords):
        if current_user.role not in ('hr', 'admin'):
            # 员工无权发布公告
            answer = "抱歉，您没有发布公告的权限。只有 HR 和管理员可以发布公告。\n\n如需发布公告，请联系 HR 部门。"
            record = QARecord(
                user_id=current_user.id,
                question=question,
                answer=answer,
                answer_type="no_permission",
                source_docs=json.dumps([]),
                conversation_id=conv_id
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return success({
                "answer": answer,
                "answer_type": "no_permission",
                "intent": "notice_publish",
                "source_docs": [],
                "record_id": record.id,
                "conversation_id": conv_id,
                "required_slots": [],
                "filled_slots": {},
                "actions": []
            })
        else:
            # HR发布公告 - 引导到后台页面
            answer = "通知公告发布请前往 HR 后台的「通知发布」页面操作，支持设置类型、置顶等功能。\n\n如需在聊天中快速发布，请直接告诉我公告标题和内容。"
            record = QARecord(
                user_id=current_user.id,
                question=question,
                answer=answer,
                answer_type="notice_clarification",
                source_docs=json.dumps([]),
                conversation_id=conv_id
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return success({
                "answer": answer,
                "answer_type": "notice_clarification",
                "intent": "notice_publish",
                "source_docs": [],
                "record_id": record.id,
                "conversation_id": conv_id,
                "required_slots": [],
                "filled_slots": {},
                "actions": []
            })

    # Step 7: 【第四优先级】判断是否需要年假澄清
    if is_annual_leave_days_question(question):
        # 检查是否同时提供了工龄信息（用户可能一次性说完）
        slots = extract_slots_for_intent(question, "annual_leave_calculation")
        if slots.get("work_years") and slots["work_years"] > 0:
            # 用户一次性提供了工龄信息，直接计算年假
            work_years = slots["work_years"]

            if work_years < 1:
                annual_leave = 0
                answer = "根据您提供的信息，您的工龄不足1年，暂不享受带薪年假。\n\n"
                answer += "根据公司制度，员工入职满1年后可享受带薪年假。"
            elif work_years < 10:
                annual_leave = 5
            elif work_years < 20:
                annual_leave = 10
            else:
                annual_leave = 15

            if annual_leave > 0:
                answer = f"根据您提供的信息，您的工龄约为 **{work_years}年**。\n\n"
                answer += "按照公司年假制度：\n"
                answer += "- 工龄1-10年：5天年假\n"
                answer += "- 工龄10-20年：10天年假\n"
                answer += "- 工龄20年以上：15天年假\n\n"
                answer += f"**您目前享有 {annual_leave} 天年假。**\n\n"
                answer += "温馨提示：年假需提前申请，请合理安排。"

            source_docs = [{"source": "年假制度", "document": "休假与年假管理办法"}]
            result = _save_policy_response(
                db, current_user.id, conv_id, question, answer, source_docs,
                history=get_conversation_context(db, current_user.id, conv_id),
            )
            payload = result.get("data") or {}
            payload["intent"] = "annual_leave_calculation"
            payload["filled_slots"] = slots
            return success(payload)
        else:
            # 用户没有提供工龄信息，进入澄清流程
            return handle_annual_leave_clarification(question, conv_id, current_user.id, db)

    # Step 8: 【原有逻辑】关键词匹配FAQ
    # 使用 resolved_question 进行匹配（如果是 follow-up 问题）
    context = get_conversation_context(db, current_user.id, conv_id)

    conversation_topic = recent_context.get("conversation_topic") or recent_context.get("last_topic", "")

    # 含具体工龄的工龄福利问题：优先计算，不走 FAQ 泛化回答
    welfare_calc_result = _try_seniority_welfare_followup_answer(
        db, current_user.id, conv_id, question, resolved_question,
        followup_context if is_followup else {},
        conversation_topic=conversation_topic,
    )
    if welfare_calc_result:
        return _attach_paused_notice(welfare_calc_result)

    faq = match_faq(db, resolved_question, conversation_topic=conversation_topic)

    # 证明/工单语境：拒绝误匹配的 FAQ（如绩效申诉）
    if faq and _ticket_context_active(state, recent_context):
        if is_ticket_confirm_intent(question, data.action) or is_ticket_validation_intent(question) or is_ticket_info_query(question):
            faq = None
        else:
            faq_text = (faq.question or "") + (faq.answer or "") + (faq.keywords or "")
            if not any(k in faq_text for k in ("证明", "在职", "工单", "开具", "HR")):
                if any(k in faq_text for k in ("绩效", "申诉", "请假", "年假", "考勤")):
                    faq = None
                elif "提交" in question and "提交" in (faq.question or ""):
                    faq = None

    # 证明办理语境：拒绝明显无关的 FAQ（如绩效申诉）
    if faq and conversation_topic == "certify_ticket":
        faq_text = (faq.question or "") + (faq.answer or "") + (faq.keywords or "")
        if not any(k in faq_text for k in ("证明", "在职", "工单", "开具", "HR")):
            if any(k in faq_text for k in ("绩效", "申诉", "请假", "年假", "考勤")):
                faq = None

    # follow-up 问题的主题验证：确保匹配的 FAQ 与上下文主题一致
    if faq and is_followup and followup_context.get("inherited_topic"):
        topic = followup_context["inherited_topic"]
        faq_text = (faq.question + " " + (faq.answer or "") + " " + (faq.keywords or "")).lower()

        # 主题关键词验证
        topic_keywords = {
            "annual_leave": ["年假", "工龄", "年休假", "带薪"],
            "leave_application": ["请假", "病假", "事假", "假期", "休假"],
            "attendance": ["考勤", "打卡", "迟到", "加班"],
            "salary": ["工资", "薪资", "社保", "报销"],
            "salary_welfare": ["福利", "工龄", "年终奖", "礼金", "补贴"],
            "probation": ["试用", "转正"],
        }

        expected_keywords = topic_keywords.get(topic, [])
        if expected_keywords and not any(kw in faq_text for kw in expected_keywords):
            faq = None

    # 非 followup 但会话主题明确时，拒绝明显不相关的 FAQ
    if faq and conversation_topic == "salary_welfare":
        faq_text = (faq.question or "") + (faq.keywords or "")
        if not any(k in faq_text for k in ("福利", "工龄", "年终奖", "礼金")):
            if any(k in faq_text for k in ("文档", "AI", "查重")):
                faq = None

    if faq:
        context_hint = _followup_context_hint(followup_context) if is_followup else ""
        return _attach_paused_notice(_save_faq_response(
            db, current_user.id, conv_id, question, faq,
            history=context, context_hint=context_hint,
        ))

    # Step 10: 【原有逻辑】关键词匹配规则
    rule = match_rule(db, resolved_question)

    # follow-up 问题的主题验证：确保匹配的规则与上下文主题一致
    if rule and is_followup and followup_context.get("inherited_topic"):
        topic = followup_context["inherited_topic"]
        rule_text = (rule.name + " " + (rule.trigger_keywords or "") + " " + (rule.answer_template or "")).lower()

        # 主题关键词验证
        topic_keywords = {
            "annual_leave": ["年假", "工龄", "年休假", "带薪"],
            "leave_application": ["请假", "病假", "事假", "假期", "休假"],
            "attendance": ["考勤", "打卡", "迟到", "加班"],
            "salary": ["工资", "薪资", "社保", "报销"],
        }

        expected_keywords = topic_keywords.get(topic, [])
        if expected_keywords and not any(kw in rule_text for kw in expected_keywords):
            # 规则与主题不匹配，不使用这个规则
            rule = None

    if rule:
        context_hint = _followup_context_hint(followup_context) if is_followup else ""
        return _attach_paused_notice(_save_rule_response(
            db, current_user.id, conv_id, question, rule,
            history=context, context_hint=context_hint,
        ))

    # Step 11: 【原有逻辑】RAG搜索 + AI生成
    # 使用 resolved_question 进行搜索（如果是 follow-up 问题）
    intent_context_hint = ""
    if conversation_topic == "certify_ticket" or followup_context.get("is_ticket_question"):
        intent_context_hint = "用户正在办理在职证明/工单，当前问题可能是工单相关追问。"
    elif context:
        intent_context_hint = context[-500:]

    skip_clarification = (
        (is_followup and was_followup_rewritten(question, followup_context))
        or conversation_topic == "certify_ticket"
        or followup_context.get("is_ticket_question")
        or (state and state.pending_intent == "ticket_create")
    )
    answer, sources, confidence = rag_search_and_generate(
        resolved_question,
        context,
        skip_intent_clarification=skip_clarification,
        context_hint=intent_context_hint,
    )

    if confidence == "need_clarification":
        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=answer,
            answer_type="clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "clarification",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": []
        })

    if confidence == "low_confidence":
        # 未改写的短追问不应写入 qa_miss
        if is_unresolved_followup(question, is_followup, followup_context):
            answer = (
                followup_context.get("clarification_message")
                or build_no_context_clarification(question)
            )
            return _save_clarification_response(
                db, current_user.id, conv_id, question, answer, "followup_clarification"
            )

        # 已改写的考勤追问：政策兜底，不写 qa_miss
        policy_result = _try_attendance_followup_answer(
            db, current_user.id, conv_id, question, resolved_question, followup_context
        )
        if policy_result:
            return policy_result

        annual_result = _try_annual_leave_followup_answer(
            db, current_user.id, conv_id, question, resolved_question, followup_context
        )
        if annual_result:
            return annual_result

        # 其他已改写的主题追问：返回上下文提示，不写 qa_miss
        if was_followup_rewritten(question, followup_context):
            topic = followup_context.get("inherited_topic", "")
            answer = (
                f"关于「{resolved_question}」，当前知识库暂未找到完整依据。\n\n"
                "建议您：\n"
                "1. 换个关键词重新提问\n"
                "2. 联系 HR 部门获取帮助\n"
                "3. 提交工单进行详细咨询"
            )
            if topic == "attendance":
                answer += "\n\n如需提交考勤相关说明，可以说「我想提交考勤异常说明」。"
            record = QARecord(
                user_id=current_user.id,
                question=question,
                answer=answer,
                answer_type="clarification",
                source_docs=json.dumps([]),
                conversation_id=conv_id,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return success({
                "answer": answer,
                "answer_type": "clarification",
                "intent": "followup_insufficient",
                "source_docs": [],
                "record_id": record.id,
                "conversation_id": conv_id,
                "required_slots": [],
                "filled_slots": {},
                "actions": ["transfer_to_hr"],
            })

        miss = QAMiss(user_id=current_user.id, question=question)
        db.add(miss)
        db.commit()
        db.refresh(miss)

        clarification = f"抱歉，关于「{question}」，当前知识库暂未找到明确依据。\n\n建议您：\n1. 换个关键词重新提问\n2. 联系HR部门获取帮助\n3. 提交工单进行详细咨询"

        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=clarification,
            answer_type="miss",
            source_docs=json.dumps([]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _attach_paused_notice(success({
            "answer": clarification,
            "answer_type": "miss",
            "intent": "miss",
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": ["transfer_to_hr"],
            "miss_id": miss.id
        }))

    # Step 12: 【原有逻辑】高置信度回答
    record = QARecord(
        user_id=current_user.id,
        question=question,
        answer=answer,
        answer_type="rag",
        source_docs=json.dumps(sources),
        conversation_id=conv_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _attach_paused_notice(success({
        "answer": answer,
        "answer_type": "rag",
        "source_docs": sources,
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": []
    }))


@router.post("/save-record")
def save_chat_record(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """保存前端拦截的对话记录"""
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    answer_type = data.get("answer_type", "system")
    conversation_id = data.get("conversation_id")

    if not question or not answer:
        return error("问题和回答不能为空")

    if not conversation_id:
        conversation_id = str(uuid.uuid4())[:16]

    record = QARecord(
        user_id=current_user.id,
        question=question,
        answer=answer,
        answer_type=answer_type,
        source_docs=json.dumps([]),
        conversation_id=conversation_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success({
        "record_id": record.id,
        "conversation_id": conversation_id
    })


@router.post("/voice")
def voice_chat(current_user: User = Depends(get_current_user)):
    mock_text = "语音识别结果：请问公司的年假政策是什么？"
    return success({
        "recognized_text": mock_text,
        "answer": "【语音问答Mock】\n\n根据公司制度，年假按照工龄计算：\n- 工龄1-10年：5天\n- 工龄10-20年：10天\n- 工龄20年以上：15天\n\n温馨提示：年假需提前申请，请合理安排。",
        "answer_type": "mock"
    })


@router.post("/image")
def image_chat(current_user: User = Depends(get_current_user)):
    mock_text = "OCR识别结果：报销单据"
    return success({
        "ocr_text": mock_text,
        "answer": "【图片问答Mock】\n\n已识别图片内容为报销单据。报销流程如下：\n1. 填写报销申请表\n2. 附上发票原件\n3. 部门主管审批\n4. 财务审核\n5. 打款\n\n温馨提示：报销需在消费后30天内提交。",
        "answer_type": "mock"
    })


@router.get("/stats")
def get_chat_stats(current_user: User = Depends(get_current_user)):
    from app.services.rag.vectorstore import get_collection_stats
    stats = get_collection_stats()
    return success(stats)


@router.get("/category-stats")
def get_category_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取咨询类别分布统计"""
    from sqlalchemy import func
    from app.models.qa import QARecord

    stats = db.query(
        QARecord.answer_type,
        func.count(QARecord.id)
    ).group_by(QARecord.answer_type).all()

    category_map = {
        'faq': '标准答案',
        'rule': '规则匹配',
        'rag': '文档检索',
        'miss': '未命中',
        'clarification': '澄清追问',
        'ticket_form': '工单申请',
        'ticket_qa': '工单咨询',
        'ticket_submitted': '工单已提交',
        'notice_form': '公告发布',
        'notice_confirm': '公告确认',
        'no_permission': '无权限'
    }

    result = []
    for answer_type, count in stats:
        category = category_map.get(answer_type, '其他')
        result.append({
            'name': category,
            'value': count,
            'type': answer_type
        })

    result.sort(key=lambda x: x['value'], reverse=True)

    return success(result)
