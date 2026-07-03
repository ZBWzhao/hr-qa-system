import re
import json
import uuid
from datetime import datetime
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
from app.services.llm import generate_answer, analyze_intent, generate_clarification
from app.services.text_splitter import extract_keywords
from app.services.conversation_state_service import ConversationStateService
from app.services.slot_extractor import extract_slots_for_intent
from app.services.ticket_intent_service import detect_ticket_intent, TICKET_SLOT_CONFIG
from app.services.ticket_slot_extractor import extract_ticket_slots
from app.services.followup_service import is_followup_question, get_recent_context, rewrite_followup_question

router = APIRouter()


def get_or_create_conversation_id(db: Session, user_id: int, conversation_id: str = None) -> str:
    if conversation_id:
        return conversation_id
    return str(uuid.uuid4())[:16]


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

        # 保存问答记录
        # TODO: 后续升级为 rag，关联《休假与年假管理办法》文档
        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="rule",
            source_docs=json.dumps([{"source": "年假制度", "document": "休假与年假管理办法"}]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return success({
            "answer": answer,
            "answer_type": "rule",
            "intent": "annual_leave_calculation",
            "source_docs": [{"source": "年假制度", "document": "休假与年假管理办法"}],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": filled,
            "actions": []
        })

    # 未知的 pending_intent，清空并走正常流程
    state_service.clear_pending_intent(user_id, conv_id)
    return None


def handle_ticket_create(question: str, conv_id: str, user_id: int, db: Session) -> dict:
    """
    处理工单创建：识别工单意图，设置 pending_intent，返回澄清
    """
    intent_result = detect_ticket_intent(question)

    if not intent_result["is_ticket_intent"]:
        return None

    ticket_type = intent_result["ticket_type"]
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    # 尝试从第一轮提取已有字段
    slots = extract_ticket_slots(question, ticket_type)

    # 构建 filled_slots，包含 ticket_type 和 title
    filled_slots = {
        "ticket_type": ticket_type,
        "title": config["title"],
        "display_type": config["display_type"]
    }
    filled_slots.update(slots)

    # 保存状态
    state_service = ConversationStateService(db)
    state_service.set_pending_intent(
        user_id=user_id,
        conversation_id=conv_id,
        intent="ticket_create",
        required_slots=config["required_slots"]
    )

    # 始终更新已填充的槽位（包含 ticket_type 等元数据）
    state_service.update_filled_slots(user_id, conv_id, filled_slots)

    # 检查是否所有槽位都已填充
    if state_service.check_slots_filled(user_id, conv_id):
        # 槽位齐全，直接返回确认卡片
        return _build_ticket_confirm(question, conv_id, user_id, db, ticket_type, state_service)

    # 生成追问内容
    missing_slots = [s for s in config["required_slots"] if s not in filled_slots]
    answer = f"好的，我来帮您提交「{config['display_type']}」申请。\n\n"

    if missing_slots:
        answer += "还需要补充以下信息：\n"
        for i, slot in enumerate(missing_slots, 1):
            label = config["slot_labels"].get(slot, slot)
            answer += f"{i}. {label}\n"

    # 保存问答记录
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id
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
        "actions": []
    })


def handle_ticket_pending(question: str, state, user_id: int, db: Session) -> dict:
    """
    处理工单槽位补充
    """
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    # 从 filled_slots 中读取 ticket_type
    try:
        filled = json.loads(state.filled_slots) if state.filled_slots else {}
    except:
        filled = {}

    ticket_type = filled.get("ticket_type", "other")
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    # 检查是否是确认提交
    confirm_words = ['确认', '确认提交', '可以', '是的', '提交吧', '没问题', '确定', '提交', '好的']
    if question.strip() in confirm_words or question.strip().lower() in ['ok', 'yes']:
        return handle_ticket_confirm(question, state, user_id, db)

    # 检查是否是继续修改
    if question.strip() in ['继续修改', '修改', '我要修改']:
        answer = "好的，请说明你想修改哪一项，例如：\n"
        answer += "- 「接收单位改成XX」\n"
        answer += "- 「期望时间改为下周一前」\n"
        answer += "- 或者重新补充完整信息"

        record = QARecord(
            user_id=user_id,
            question=question,
            answer=answer,
            answer_type="ticket_clarification",
            source_docs=json.dumps([]),
            conversation_id=conv_id
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
            "actions": []
        })

    # 提取槽位
    slots = extract_ticket_slots(question, ticket_type)

    # 合并槽位
    for key, value in slots.items():
        if value is not None and value != "" and value != 0:
            filled[key] = value

    # 更新 filled_slots
    state_service.update_filled_slots(user_id, conv_id, filled)

    # 检查是否所有槽位都已填充
    if state_service.check_slots_filled(user_id, conv_id):
        # 槽位齐全，返回确认卡片
        return _build_ticket_confirm(question, conv_id, user_id, db, ticket_type, state_service)

    # 继续追问缺失字段
    missing_slots = [s for s in config["required_slots"] if s not in filled]
    answer = "还需要补充以下信息：\n"
    for i, slot in enumerate(missing_slots, 1):
        label = config["slot_labels"].get(slot, slot)
        answer += f"{i}. {label}\n"

    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_clarification",
        source_docs=json.dumps([]),
        conversation_id=conv_id
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
        "actions": []
    })


def _build_ticket_confirm(question: str, conv_id: str, user_id: int, db: Session, ticket_type: str, state_service: ConversationStateService) -> dict:
    """构建工单确认卡片"""
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])
    filled = state_service.get_filled_slots(user_id, conv_id)

    # 构建描述
    desc_parts = []
    for slot in config["required_slots"]:
        label = config["slot_labels"].get(slot, slot)
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else "否"
        if value:
            desc_parts.append(f"{label}：{value}")

    description = "\n".join(desc_parts)

    # 构建确认回答
    answer = f"请确认以下工单信息：\n\n"
    answer += f"**工单类型：** {config['display_type']}\n"
    answer += f"**标题：** {config['title']}\n"
    for slot in config["required_slots"]:
        label = config["slot_labels"].get(slot, slot)
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else "否"
        if value:
            answer += f"**{label}：** {value}\n"
    answer += f"\n确认提交给 HR 吗？"

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
            "title": config["title"],
            "description": description,
            "fields": {k: v for k, v in filled.items() if k not in ["ticket_type", "title", "display_type"]}
        },
        "actions": [
            {"type": "confirm_submit", "label": "确认提交"},
            {"type": "modify", "label": "继续修改"}
        ]
    })


def _answer_ticket_question(question: str, ticket_type: str, config: dict, filled: dict) -> str:
    """
    回复工单确认阶段的用户问题
    """
    q = question.strip()
    q_lower = q.lower()

    # 办理时间相关
    if any(kw in q for kw in ['多久', '时间', '几天', '多长时间', '办理时间']):
        return "一般由 HR 根据实际工作量处理，通常建议预留 1-3 个工作日。\n\n当前工单尚未提交，如信息无误请点击「确认提交」；如需修改请点击「继续修改」。"

    # 进度查询
    if any(kw in q for kw in ['进度', '查看', '怎么查', '在哪看']):
        return "工单提交后，你可以在「我的 - 人工请求」中查看处理进度。\n\n当前工单尚未提交，如信息无误请点击「确认提交」。"

    # 修改相关
    if any(kw in q for kw in ['修改', '改', '变更', '更正']):
        return "如需修改工单信息，请点击「继续修改」按钮，然后告诉我需要修改的内容。\n\n当前工单尚未提交。"

    # 材料相关
    if any(kw in q for kw in ['材料', '资料', '文件', '需要什么']):
        return "具体所需材料请以 HR 部门要求为准。如有疑问，可在提交后联系 HR 确认。\n\n当前工单尚未提交，如信息无误请点击「确认提交」。"

    # 通知相关
    if any(kw in q for kw in ['通知', '告知', '提醒', '会通知']):
        return "工单提交后，HR 会收到通知并尽快处理。处理完成后系统会通知你。\n\n当前工单尚未提交，如信息无误请点击「确认提交」。"

    # 通用回答
    return "当前工单尚未提交，如信息无误请点击「确认提交」；如需修改请点击「继续修改」。如有其他问题，请先提交工单后联系 HR 咨询。"


def handle_ticket_confirm(question: str, state, user_id: int, db: Session, action: str = None) -> dict:
    """
    处理工单确认提交

    只有明确的确认词或 action=confirm_submit 才会提交工单
    其他问题会回答但保持 waiting_for_confirm 状态
    """
    state_service = ConversationStateService(db)
    conv_id = state.conversation_id

    # 从 filled_slots 读取信息
    try:
        filled = json.loads(state.filled_slots) if state.filled_slots else {}
    except:
        filled = {}

    ticket_type = filled.get("ticket_type", "other")
    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    # 严格的确认词列表
    strict_confirm_words = [
        '确认', '确认提交', '提交', '提交吧', '可以提交',
        '没问题', '是的', '确认无误', '好的', '可以', '行'
    ]

    # 检查是否是真正的确认操作
    is_confirm = False
    if action == "confirm_submit":
        is_confirm = True
    elif question.strip() in strict_confirm_words:
        is_confirm = True
    elif question.strip().lower() in ['ok', 'yes', 'confirm']:
        is_confirm = True

    # 如果不是确认操作，回答用户问题但保持状态
    if not is_confirm:
        # 根据用户问题生成回答
        answer = _answer_ticket_question(question, ticket_type, config, filled)

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

        # 构建 ticket_draft
        desc_parts = []
        for slot in config["required_slots"]:
            label = config["slot_labels"].get(slot, slot)
            value = filled.get(slot, "")
            if slot == "need_stamp":
                value = "是" if value else "否"
            if value:
                desc_parts.append(f"{label}：{value}")

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
                "title": config["title"],
                "description": "\n".join(desc_parts),
                "fields": {k: v for k, v in filled.items() if k not in ["ticket_type", "title", "display_type"]}
            },
            "actions": [
                {"type": "confirm_submit", "label": "确认提交"},
                {"type": "modify", "label": "继续修改"}
            ]
        })

    # 以下是确认提交的逻辑
    # 构建工单描述
    desc_parts = []
    for slot in config["required_slots"]:
        label = config["slot_labels"].get(slot, slot)
        value = filled.get(slot, "")
        if slot == "need_stamp":
            value = "是" if value else "否"
        if value:
            desc_parts.append(f"{label}：{value}")

    description = "\n".join(desc_parts)

    # 生成工单编号
    ticket_count = db.query(Ticket).count()
    ticket_no = f"TK{datetime.now().strftime('%Y%m%d')}{ticket_count + 1:04d}"

    # 创建工单
    ticket = Ticket(
        ticket_no=ticket_no,
        type=ticket_type,
        title=config["title"],
        description=description,
        status="pending",
        creator_id=user_id,
        conversation_id=conv_id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 清空 pending_intent
    state_service.clear_pending_intent(user_id, conv_id)

    # 生成回答
    answer = f"已提交人工请求，工单编号：**{ticket_no}**。\n\n"
    answer += f"你可以在「我的 - 人工请求」中查看处理进度。"

    # 保存问答记录
    record = QARecord(
        user_id=user_id,
        question=question,
        answer=answer,
        answer_type="ticket_submitted",
        source_docs=json.dumps([]),
        conversation_id=conv_id
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
            "status": "pending"
        },
        "actions": []
    })


def match_faq(db: Session, question: str):
    """关键词匹配FAQ，不调用API"""
    keywords = extract_keywords(question)
    faqs = db.query(FAQ).filter(FAQ.status == 1).all()

    common_words = {'如何', '怎么', '什么', '为什么', '请', '帮我', '告诉', '一下',
                    '一些', '这个', '那个', '可以', '能否', '是否', '有没有', '想',
                    '知道', '了解', '咨询', '询问', '问', '答', '回答', '问题'}

    best_match = None
    best_score = 0

    q_lower = question.lower()

    for faq in faqs:
        score = 0

        if faq.question and (faq.question.lower() in q_lower or q_lower in faq.question.lower()):
            score += 10

        for kw in keywords:
            if not kw:
                continue

            is_common = kw in common_words
            weight = 1 if is_common else 3

            if faq.question and kw in faq.question:
                score += weight
            if faq.keywords and kw in faq.keywords:
                score += weight

        if score > best_score:
            best_score = score
            best_match = faq

    if best_match and best_score >= 3:
        matched_keywords = []
        for kw in keywords:
            if kw and ((faq.question and kw in faq.question) or (faq.keywords and kw in faq.keywords)):
                matched_keywords.append(kw)

        all_common = all(kw in common_words for kw in matched_keywords if kw)
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


def rag_search_and_generate(question: str, history: str = "") -> tuple:
    """RAG搜索 + AI生成回答"""

    intent_result = analyze_intent(question)

    if intent_result.get("need_clarification", False):
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

    # Step 4: 【第一优先级】检查 pending_intent
    if state.pending_intent:
        # 工单待确认状态
        if state.pending_intent == "ticket_create" and state.status == "waiting_for_confirm":
            result = handle_ticket_confirm(question, state, current_user.id, db, data.action)
            if result:
                return result

        # 工单槽位补充状态
        if state.pending_intent == "ticket_create":
            result = handle_ticket_pending(question, state, current_user.id, db)
            if result:
                return result

        # 年假补充信息状态
        if state.pending_intent == "annual_leave_calculation":
            result = handle_pending_intent(question, state, current_user.id, db)
            if result:
                return result

        # 其他未知的 pending_intent，清空并走正常流程
        state_service.clear_pending_intent(current_user.id, conv_id)

    # Step 5: 【新增】上下文追问处理
    resolved_question = question
    is_followup = False
    followup_context = {}

    if is_followup_question(question):
        recent_context = get_recent_context(current_user.id, conv_id, db)
        if recent_context.get("last_topic"):
            followup_result = rewrite_followup_question(question, recent_context)
            if followup_result.get("is_followup"):
                is_followup = True
                followup_context = followup_result

                # 如果需要澄清
                if followup_result.get("need_clarification"):
                    answer = followup_result.get("clarification_message", "请补充更完整的问题。")
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
                        "intent": "followup_clarification",
                        "source_docs": [],
                        "record_id": record.id,
                        "conversation_id": conv_id,
                        "required_slots": [],
                        "filled_slots": {},
                        "actions": []
                    })

                # 使用改写后的问题
                if followup_result.get("resolved_question"):
                    resolved_question = followup_result["resolved_question"]

    # Step 6: 【第二优先级】判断是否是工单意图
    ticket_result = handle_ticket_create(question, conv_id, current_user.id, db)
    if ticket_result:
        return ticket_result

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

            # TODO: 后续升级为 rag，关联《休假与年假管理办法》文档
            record = QARecord(
                user_id=current_user.id,
                question=question,
                answer=answer,
                answer_type="rule",
                source_docs=json.dumps([{"source": "年假制度", "document": "休假与年假管理办法"}]),
                conversation_id=conv_id
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return success({
                "answer": answer,
                "answer_type": "rule",
                "intent": "annual_leave_calculation",
                "source_docs": [{"source": "年假制度", "document": "休假与年假管理办法"}],
                "record_id": record.id,
                "conversation_id": conv_id,
                "required_slots": [],
                "filled_slots": slots,
                "actions": []
            })
        else:
            # 用户没有提供工龄信息，进入澄清流程
            return handle_annual_leave_clarification(question, conv_id, current_user.id, db)

    # Step 8: 【原有逻辑】关键词匹配FAQ
    # 使用 resolved_question 进行匹配（如果是 follow-up 问题）
    context = get_conversation_context(db, current_user.id, conv_id)

    faq = match_faq(db, resolved_question)

    # follow-up 问题的主题验证：确保匹配的 FAQ 与上下文主题一致
    if faq and is_followup and followup_context.get("inherited_topic"):
        topic = followup_context["inherited_topic"]
        faq_text = (faq.question + " " + (faq.answer or "")).lower()

        # 主题关键词验证
        topic_keywords = {
            "annual_leave": ["年假", "工龄", "年休假", "带薪"],
            "leave_application": ["请假", "病假", "事假", "假期", "休假"],
            "attendance": ["考勤", "打卡", "迟到", "加班"],
            "salary": ["工资", "薪资", "社保", "报销"],
        }

        expected_keywords = topic_keywords.get(topic, [])
        if expected_keywords and not any(kw in faq_text for kw in expected_keywords):
            # FAQ 与主题不匹配，不使用这个 FAQ
            faq = None

    if faq:
        # 如果是 follow-up，在回答中说明上下文
        if is_followup and followup_context.get("inherited_topic"):
            topic_names = {
                "annual_leave": "年假",
                "leave_application": "请假",
                "attendance": "考勤",
                "salary": "薪酬"
            }
            topic_name = topic_names.get(followup_context["inherited_topic"], "")
            answer = f"结合您之前关于{topic_name}的问题，"
            answer += f"我理解您的问题是关于「{faq.question}」。\n\n"
        else:
            answer = f"我理解您的问题是关于「{faq.question}」。\n\n"
        answer += f"根据标准答案库查询，找到以下相关信息：\n\n"
        answer += f"**问题：** {faq.question}\n\n"
        answer += f"**答案：** {faq.answer}"
        record = QARecord(
            user_id=current_user.id,
            question=question,  # 保存原始问题
            answer=answer,
            answer_type="faq",
            source_docs=json.dumps([{"faq_id": faq.id, "question": faq.question}]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "faq",
            "source_docs": [{"faq_id": faq.id, "question": faq.question}],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": []
        })

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
        answer = f"我理解您的问题，根据公司相关规则查询：\n\n"
        answer += f"**规则名称：** {rule.name}\n\n"
        answer += f"**规定内容：**\n{rule.answer_template}"
        record = QARecord(
            user_id=current_user.id,
            question=question,
            answer=answer,
            answer_type="rule",
            source_docs=json.dumps([{"rule_id": rule.id, "name": rule.name}]),
            conversation_id=conv_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success({
            "answer": answer,
            "answer_type": "rule",
            "source_docs": [{"rule_id": rule.id, "name": rule.name}],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": []
        })

    # Step 11: 【原有逻辑】RAG搜索 + AI生成
    # 使用 resolved_question 进行搜索（如果是 follow-up 问题）
    answer, sources, confidence = rag_search_and_generate(resolved_question, context)

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
        return success({
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
        })

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
    return success({
        "answer": answer,
        "answer_type": "rag",
        "source_docs": sources,
        "record_id": record.id,
        "conversation_id": conv_id,
        "required_slots": [],
        "filled_slots": {},
        "actions": []
    })


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
