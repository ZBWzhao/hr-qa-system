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
from app.services.rag.vectorstore import search_similar
from app.services.llm import generate_answer, analyze_intent, generate_clarification
from app.services.text_splitter import extract_keywords
from app.services.conversation_state_service import ConversationStateService
from app.services.slot_extractor import extract_slots_for_intent

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
        result = handle_pending_intent(question, state, current_user.id, db)
        if result:
            return result
        # 如果 handle_pending_intent 返回 None，说明是未知的 pending_intent，继续走正常流程

    # Step 5: 【第二优先级】判断是否需要年假澄清
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

    # Step 6: 【原有逻辑】关键词匹配FAQ
    context = get_conversation_context(db, current_user.id, conv_id)

    faq = match_faq(db, question)
    if faq:
        answer = f"我理解您的问题是关于「{faq.question}」。\n\n"
        answer += f"根据标准答案库查询，找到以下相关信息：\n\n"
        answer += f"**问题：** {faq.question}\n\n"
        answer += f"**答案：** {faq.answer}"
        record = QARecord(
            user_id=current_user.id,
            question=question,
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

    # Step 7: 【原有逻辑】关键词匹配规则
    rule = match_rule(db, question)
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

    # Step 8: 【原有逻辑】RAG搜索 + AI生成
    answer, sources, confidence = rag_search_and_generate(question, context)

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
            "source_docs": [],
            "record_id": record.id,
            "conversation_id": conv_id,
            "required_slots": [],
            "filled_slots": {},
            "actions": []
        })

    # Step 9: 【原有逻辑】高置信度回答
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
