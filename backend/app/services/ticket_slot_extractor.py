"""
工单槽位提取器
用于从用户输入中提取工单相关的结构化信息
"""
import re
from typing import Dict, Any, Optional


def extract_ticket_slots(text: str, ticket_type: str) -> Dict[str, Any]:
    """
    从文本中提取工单槽位

    Args:
        text: 用户输入文本
        ticket_type: 工单类型 (certify/info_change/attendance_exception/other)

    Returns:
        提取到的槽位字典
    """
    if ticket_type == "certify":
        return _extract_certify_slots(text)
    elif ticket_type == "info_change":
        return _extract_info_change_slots(text)
    elif ticket_type == "attendance_exception":
        return _extract_attendance_exception_slots(text)
    else:
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
        r'接收单位[是为]?([^，,。.、]{2,20})',
        r'提交给([^，,。.、]{2,20})',
        r'给([^，,。.、]{2,15})领事馆',
        r'给([^，,。.、]{2,15})公司',
        r'给([^，,。.、]{2,15})银行',
        r'接收方[是为]?([^，,。.、]{2,20})',
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


def _extract_attendance_exception_slots(text: str) -> Dict[str, Any]:
    """提取考勤异常槽位"""
    result = {}

    # 提取 exception_date（异常日期）
    date_patterns = [
        r'(\d+月\d+[日号])',
        r'(\d{4}[.\-/年]\d{1,2}[.\-/月]\d{1,2}[日号]?)',
        r'([今昨前明][天日])',
        r'([本上][周月]\d+[日号])',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            result['exception_date'] = match.group(1)
            break

    # 提取 exception_type（异常类型）
    type_keywords = {
        '忘记打卡': ['忘记打卡', '忘打卡', '漏打卡', '没打卡'],
        '迟到': ['迟到'],
        '早退': ['早退'],
        '缺卡': ['缺卡'],
    }
    for etype, keywords in type_keywords.items():
        if any(kw in text for kw in keywords):
            result['exception_type'] = etype
            break

    # 提取 reason（异常原因）
    reason_patterns = [
        r'因为(.{2,30})',
        r'原因是(.{2,30})',
        r'由于(.{2,30})',
        r'因为(.{2,30})',
    ]
    for pattern in reason_patterns:
        match = re.search(pattern, text)
        if match:
            reason = match.group(1).strip()
            reason = re.sub(r'[，,。.]$', '', reason)
            result['reason'] = reason
            break

    # description（补充说明）
    result['description'] = text

    return result


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
