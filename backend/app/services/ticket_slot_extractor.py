"""
工单槽位提取器
优先使用 AI 理解用户自然语言，失败时回退到规则/正则
"""
import re
from typing import Dict, Any, Optional

from app.services.llm import extract_ticket_slots_with_ai
from app.services.ticket_intent_service import TICKET_SLOT_CONFIG


_SKIP_SLOT_PHRASES = {
    "确认", "确认提交", "确认无误", "提交", "提交吧", "提交工单", "可以提交", "没问题",
    "手动填写", "手动填写工单", "已手动填写工单",
    "继续修改", "我要修改", "修改工单", "改一下", "重新填写",
    "取消", "不办了", "放弃", "算了",
}


def _skip_slot_extraction(text: str) -> bool:
    q = text.strip()
    return q in _SKIP_SLOT_PHRASES


def extract_ticket_slots(
    text: str,
    ticket_type: str,
    filled: Optional[Dict[str, Any]] = None,
    *,
    prefer_llm: bool = True,
) -> Dict[str, Any]:
    """
    从文本中提取工单槽位（结构化规则优先，AI 补充，规则兜底）
    """
    if _skip_slot_extraction(text):
        return {}

    config = TICKET_SLOT_CONFIG.get(ticket_type, TICKET_SLOT_CONFIG["other"])

    # 考勤异常：逗号分隔输入用确定性规则，避免 AI 把类型/原因搞混
    if ticket_type == "attendance_exception":
        structured = _parse_attendance_comma_segments(text)
        if structured:
            return _finalize_slots(ticket_type, structured)

    if prefer_llm:
        ai_slots = extract_ticket_slots_with_ai(text, ticket_type, config, filled)
        if ai_slots:
            ai_slots = _sanitize_attendance_slots(ai_slots, text, ticket_type)
            return _finalize_slots(ticket_type, ai_slots)

    regex_slots = _extract_ticket_slots_regex(text, ticket_type)
    regex_slots = _sanitize_attendance_slots(regex_slots, text, ticket_type)
    return _finalize_slots(ticket_type, regex_slots)


def _sanitize_attendance_slots(slots: Dict[str, Any], text: str, ticket_type: str) -> Dict[str, Any]:
    """若原因字段被填成整句，尝试用逗号规则重新解析"""
    if ticket_type != "attendance_exception" or not slots:
        return slots
    reason = str(slots.get("reason") or "")
    if ("," in reason or "，" in reason) and re.search(r"\d{4}", reason):
        structured = _parse_attendance_comma_segments(text)
        if structured:
            return structured
    # 类型误填成「忘记打卡」但原文含「打卡缺失」时，以逗号分段为准
    if slots.get("exception_type") == "忘记打卡" and "打卡缺失" in text:
        structured = _parse_attendance_comma_segments(text)
        if structured:
            return structured
    return slots


def _finalize_slots(ticket_type: str, slots: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(slots)
    if ticket_type == "attendance_exception" and result.get("reason"):
        result["description"] = result["reason"]
    return result


def _extract_ticket_slots_regex(text: str, ticket_type: str) -> Dict[str, Any]:
    if ticket_type == "certify":
        return _extract_certify_slots(text)
    elif ticket_type == "info_change":
        return _extract_info_change_slots(text)
    elif ticket_type == "attendance_exception":
        return _extract_attendance_exception_slots(text)
    return _extract_other_slots(text)


def _extract_certify_slots(text: str) -> Dict[str, Any]:
    """提取证明开具槽位"""
    result = {}

    # 提取 purpose（证明用途）
    purpose_patterns = [
        r'用于([^，,。.、]{2,20})',
        r'用途[是为]([^，,。.、]{2,20})',
        r'用来([^，,。.、]{2,20})',
        r'是为了([^，,。.、]{2,20})',
    ]
    for pattern in purpose_patterns:
        match = re.search(pattern, text)
        if match:
            purpose = match.group(1).strip()
            result['purpose'] = purpose
            break

    # 提取 receiver（接收单位）
    receiver_patterns = [
        r'接收单位[是为]?([^，,。.、]{2,30})',
        r'提交给([^，,。.、]{2,30})',
        r'交给([^，,。.、]{2,30}?)(?:领事馆|大使馆|银行|公司|单位)',
        r'给([^，,。.、]{2,20})领事馆',
        r'给([^，,。.、]{2,20})公司',
        r'给([^，,。.、]{2,20})银行',
        r'接收方[是为]?([^，,。.、]{2,30})',
    ]
    for pattern in receiver_patterns:
        match = re.search(pattern, text)
        if match:
            receiver = match.group(1).strip()
            result['receiver'] = receiver
            break

    # 提取 need_stamp（是否需要盖章）
    if any(kw in text for kw in ['需要盖章', '要盖章', '需要公章', '盖公章', '盖章']):
        result['need_stamp'] = True
    elif any(kw in text for kw in ['不需要盖章', '不用盖章', '不要盖章', '不盖章']):
        result['need_stamp'] = False

    # 提取 expected_time（期望完成时间）
    time_patterns = [
        r'([本这]周[一二三四五六日末天]前)',
        r'([明昨今][天日]前)',
        r'(下[周月][一二三四五六日末天]?前)',
        r'(\d+天内)',
        r'(尽快)',
        r'([本这][月年]底前)',
        r'(\d+月\d+[日号]前)',
        r'(\d+[日号]前)',
        r'(月底前)',
        r'(年前)',
    ]
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            result['expected_time'] = match.group(1)
            break

    return result


def _extract_info_change_slots(text: str) -> Dict[str, Any]:
    """提取信息变更槽位"""
    result = {}

    # 提取 change_item（变更信息类型）
    item_keywords = {
        '手机号': ['手机号', '手机', '电话号码', '联系电话', '电话'],
        '邮箱': ['邮箱', '电子邮箱', '邮件地址', 'email'],
        '地址': ['地址', '住址', '居住地址', '联系地址'],
        '紧急联系人': ['紧急联系人', '紧急联系'],
    }
    for item, keywords in item_keywords.items():
        if any(kw in text for kw in keywords):
            result['change_item'] = item
            break

    # 提取 old_value 和 new_value（原信息和新信息）
    # 模式：从A改成B / 从A改为B / A改成B
    change_pattern = r'(?:从|原[来邮手]?[是号]?)(.{5,20})(?:改成|改为|改|变成)(.{5,20})'
    match = re.search(change_pattern, text)
    if match:
        old_val = match.group(1).strip()
        new_val = match.group(2).strip()
        # 清理
        old_val = re.sub(r'[，,。.]$', '', old_val)
        new_val = re.sub(r'[，,。.]$', '', new_val)
        result['old_value'] = old_val
        result['new_value'] = new_val
    else:
        # 尝试匹配手机号/邮箱格式
        phones = re.findall(r'1[3-9]\d{9}', text)
        if len(phones) >= 2:
            result['old_value'] = phones[0]
            result['new_value'] = phones[1]
        elif len(phones) == 1:
            # 只有一个手机号，可能是新的
            result['new_value'] = phones[0]

        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
        if len(emails) >= 2:
            result['old_value'] = emails[0]
            result['new_value'] = emails[1]
        elif len(emails) == 1:
            result['new_value'] = emails[0]

    # 提取 reason（变更原因）
    reason_patterns = [
        r'原因[是为]?(.{2,30})',
        r'因为(.{2,30})',
        r'由于(.{2,30})',
    ]
    for pattern in reason_patterns:
        match = re.search(pattern, text)
        if match:
            reason = match.group(1).strip()
            reason = re.sub(r'[，,。.]$', '', reason)
            result['reason'] = reason
            break

    return result


def _looks_like_attendance_date(part: str) -> bool:
    return bool(re.search(
        r'(\d{4}[.\-/年]\d{1,2}[.\-/月]\d{1,2}[日号]?|\d+月\d+[日号]|[今昨前明][天日]|[本上][周月]\d+[日号])',
        part,
    ))


def _parse_attendance_comma_segments(text: str) -> Optional[Dict[str, Any]]:
    """解析「日期, 异常类型, 原因」类逗号分隔输入"""
    parts = [p.strip() for p in re.split(r'[,，、;；]', text) if p.strip()]
    if len(parts) < 3 or not _looks_like_attendance_date(parts[0]):
        return None

    reason = parts[2]
    reason = re.sub(r'[，,。.!！?？]+$', '', reason).strip()
    if not reason:
        return None

    return {
        'exception_date': parts[0],
        'exception_type': parts[1],
        'reason': reason,
        'description': reason,
    }


def _extract_attendance_exception_slots(text: str) -> Dict[str, Any]:
    """提取考勤异常槽位"""
    if _skip_slot_extraction(text):
        return {}

    structured = _parse_attendance_comma_segments(text)
    if structured:
        return structured

    result = {}

    # 提取 exception_date（异常日期）- 完整日期优先于「X月X日」
    date_patterns = [
        r'(\d{4}[.\-/年]\d{1,2}[.\-/月]\d{1,2}[日号]?)',
        r'(\d+月\d+[日号])',
        r'([今昨前明][天日])',
        r'([本上][周月]\d+[日号])',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            result['exception_date'] = match.group(1)
            break

    # 提取 exception_type（异常类型）- 优先匹配更具体的类型词
    type_keywords = {
        '打卡缺失': ['打卡缺失', '缺卡', '漏打卡', '没打卡'],
        '忘记打卡': ['忘记打卡', '忘打卡'],
        '迟到': ['迟到'],
        '早退': ['早退'],
        '补卡': ['补卡'],
    }
    for etype, keywords in type_keywords.items():
        if any(kw in text for kw in keywords):
            result['exception_type'] = etype
            break

    # 提取 reason（异常原因）— 禁止宽泛的「原因」匹配，避免把「改成: xxx」整段吞掉
    reason_patterns = [
        r'异常原因(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*(.+)',
        r'异常原因[：:是为]+\s*(.+)',
        r'因为(.+)',
        r'由于(.+)',
    ]
    for pattern in reason_patterns:
        match = re.search(pattern, text)
        if match:
            reason = match.group(1).strip()
            reason = re.sub(r'[，,。.!！?？]+$', '', reason)
            reason = re.sub(r'^(?:改成|改为|修改为|更新为|改到)[是为:：]*\s*', '', reason)
            reason = re.sub(r'^[：:\s]+', '', reason).strip()
            if reason:
                result['reason'] = reason
                break

    # description（补充说明）：有原因时用原因；未识别出日期/类型时才保留原文
    if result.get('reason'):
        result['description'] = result['reason']
    elif not result.get('exception_date') and not result.get('exception_type') and text.strip():
        result['description'] = text.strip()

    return result


def apply_single_missing_slot_fallback(
    question: str,
    ticket_type: str,
    config: dict,
    filled: dict,
    extracted: dict,
) -> dict:
    """
    当仅剩一个必填槽位未填、且本轮未提取到时，将用户回复作为该槽位值。
    例如只剩「异常原因」时用户回复「忘记了」或「异常原因: 忘记了」。
    """
    required = config.get("required_slots", [])
    missing = [s for s in required if not filled.get(s) and not extracted.get(s)]
    if len(missing) != 1:
        return extracted

    slot = missing[0]
    q = question.strip()
    if not q or _skip_slot_extraction(q):
        return extracted

    label = config.get("slot_labels", {}).get(slot, slot)
    value = q
    for prefix in (f"{label}：", f"{label}:", f"{label}是", f"{label}为", "异常原因：", "异常原因:", "原因：", "原因:"):
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
            break

    value = re.sub(r'[，,。.!！?？]+$', '', value).strip()
    if not value:
        return extracted

    if ticket_type == "attendance_exception" and slot in ("reason", "description"):
        structured = _parse_attendance_comma_segments(q)
        if structured and structured.get("reason"):
            value = structured["reason"]

    if slot == "need_stamp":
        if value in ("是", "要", "需要", "要盖章"):
            extracted[slot] = True
        elif value in ("否", "不", "不要", "不用", "不盖章"):
            extracted[slot] = False
    else:
        extracted[slot] = value

    return extracted


def _extract_other_slots(text: str) -> Dict[str, Any]:
    """提取其他类型槽位"""
    result = {}

    # issue_type（问题类型）
    if '考勤' in text:
        result['issue_type'] = '考勤问题'
    elif '报销' in text:
        result['issue_type'] = '报销问题'
    elif '社保' in text:
        result['issue_type'] = '社保问题'
    else:
        result['issue_type'] = '其他问题'

    # description（问题说明）
    result['description'] = text

    # expected_time（期望处理时间）
    time_patterns = [
        r'([本这]周[一二三四五六日末天]前)',
        r'([明昨今][天日]前)',
        r'(下[周月][一二三四五六日末天]?前)',
        r'(\d+天内)',
        r'(尽快)',
    ]
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            result['expected_time'] = match.group(1)
            break

    return result
