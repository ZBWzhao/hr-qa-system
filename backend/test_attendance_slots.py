"""考勤异常工单槽位提取测试"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ticket_slot_extractor import (
    extract_ticket_slots,
    apply_single_missing_slot_fallback,
)
from app.services.ticket_intent_service import TICKET_SLOT_CONFIG


def test_attendance_reason_with_label():
    slots = extract_ticket_slots("异常原因: 忘记了", "attendance_exception", prefer_llm=False)
    assert slots.get("reason") == "忘记了", slots
    print("[PASS] reason with label")


def test_attendance_date_and_type():
    slots = extract_ticket_slots("2026年7月3日, 忘记打卡", "attendance_exception", prefer_llm=False)
    assert slots.get("exception_date") == "2026年7月3日", slots
    assert slots.get("exception_type") == "忘记打卡", slots
    print("[PASS] date and type")


def test_attendance_comma_separated_full():
    text = "2026年7月3日, 打卡缺失, 忘记打卡"
    slots = extract_ticket_slots(text, "attendance_exception", prefer_llm=False)
    assert slots.get("exception_date") == "2026年7月3日", slots
    assert slots.get("exception_type") == "打卡缺失", slots
    assert slots.get("reason") == "忘记打卡", slots
    assert slots.get("description") == "忘记打卡", slots
    print("[PASS] comma separated full input")


def test_single_missing_slot_fallback():
    config = TICKET_SLOT_CONFIG["attendance_exception"]
    filled = {
        "ticket_type": "attendance_exception",
        "exception_date": "2026年7月3日",
        "exception_type": "打卡缺失",
    }
    extracted = apply_single_missing_slot_fallback("忘记了", "attendance_exception", config, filled, {})
    assert extracted.get("reason") == "忘记了", extracted
    print("[PASS] single missing slot fallback")


def test_confirm_phrase_not_slot():
    slots = extract_ticket_slots("确认提交", "attendance_exception", prefer_llm=False)
    assert slots == {}, slots
    print("[PASS] confirm phrase not slot")


def test_sanitize_wrong_ai_style_parse():
    """AI 误把整句塞进 reason 时，应被逗号规则纠正"""
    wrong = {
        "exception_date": "2026年7月3日",
        "exception_type": "忘记打卡",
        "reason": "2026年7月3日, 打卡缺失, 忘记打卡",
    }
    text = "2026年7月3日, 打卡缺失, 忘记打卡"
    from app.services.ticket_slot_extractor import _sanitize_attendance_slots
    fixed = _sanitize_attendance_slots(wrong, text, "attendance_exception")
    assert fixed.get("exception_type") == "打卡缺失", fixed
    assert fixed.get("reason") == "忘记打卡", fixed
    print("[PASS] sanitize wrong parse")


def test_field_change_gai_cheng():
    from app.services.ticket_flow_service import _regex_attendance_field_updates
    for text in ("异常原因改成: 忘记", "异常原因改成忘记"):
        updates = _regex_attendance_field_updates(text)
        assert updates.get("reason") == "忘记", (text, updates)
    print("[PASS] field change 改成")


def test_attendance_field_update_regex():
    from app.services.ticket_flow_service import _regex_attendance_field_updates, is_ticket_modify_intent

    assert is_ticket_modify_intent("修改异常原因为: 忘记") is False
    updates = _regex_attendance_field_updates("修改异常原因为: 忘记, 修改补充说明为: 无")
    assert updates.get("reason") == "忘记", updates
    assert updates.get("description") == "无", updates
    print("[PASS] attendance field update regex")


if __name__ == "__main__":
    test_attendance_reason_with_label()
    test_attendance_date_and_type()
    test_attendance_comma_separated_full()
    test_single_missing_slot_fallback()
    test_confirm_phrase_not_slot()
    test_sanitize_wrong_ai_style_parse()
    test_field_change_gai_cheng()
    test_attendance_field_update_regex()
    print("ALL PASSED")