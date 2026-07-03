"""工单流程回归测试"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ticket_flow_service import (
    is_ticket_modify_intent,
    is_ticket_resume_intent,
    is_ticket_confirm_intent,
    is_ticket_validation_intent,
    is_ticket_info_query,
    is_general_question_instead_of_ticket,
    is_ticket_flow_followup,
    is_weak_ticket_reply,
    should_extract_slot_updates,
    build_ticket_modify_prompt,
    build_ticket_validation_answer,
    extract_slot_field_updates,
    answer_ticket_followup_question,
)
from app.services.ticket_slot_extractor import extract_ticket_slots
from app.services.ticket_intent_service import TICKET_SLOT_CONFIG, detect_ticket_intent, is_generic_new_ticket_intent, parse_ticket_type_choice


def test_modify_intent_with_action():
    assert is_ticket_modify_intent("继续修改", "modify") is True
    assert is_ticket_modify_intent("继续修改", None) is True
    print("[PASS] modify intent")


def test_general_qa_exit_during_certify():
    assert is_general_question_instead_of_ticket("HR 电话是多少？", "certify") is True
    assert is_general_question_instead_of_ticket("年假有几天？", "certify") is True
    assert is_general_question_instead_of_ticket(
        "用来办签证，交给日本领事馆，要盖章，最好这周五前", "certify"
    ) is False
    assert is_general_question_instead_of_ticket("继续修改", "certify") is False
    # 工单流程中的追问不应退出
    assert is_general_question_instead_of_ticket("这个大概要等几天？", "certify") is False
    assert is_general_question_instead_of_ticket("能不能加急？", "certify") is False
    assert is_general_question_instead_of_ticket("我还需要准备材料吗？", "certify") is False
    assert is_general_question_instead_of_ticket("如果周五前来不及怎么办？", "certify") is False
    assert is_general_question_instead_of_ticket("这会通知我吗？", "certify") is False
    print("[PASS] general QA exit detection")


def test_ticket_flow_followup():
    assert is_ticket_flow_followup("这个大概要等几天？", "certify") is True
    assert is_ticket_flow_followup("能不能加急？", "certify") is True
    assert is_ticket_flow_followup("我还需要准备材料吗？", "certify") is True
    assert is_ticket_flow_followup("年假有几天？", "certify") is False
    print("[PASS] ticket flow followup detection")


def test_ticket_followup_answers():
    config = TICKET_SLOT_CONFIG["certify"]
    filled = {"expected_time": "这周二前"}
    ans = answer_ticket_followup_question("这个大概要等几天？", "certify", config, filled)
    assert "1-3" in ans or "工作日" in ans
    ans2 = answer_ticket_followup_question("我还需要准备材料吗？", "certify", config, filled)
    assert "材料" in ans2
    ans3 = answer_ticket_followup_question("这会通知我吗？", "certify", config, filled)
    assert "通知" in ans3
    print("[PASS] ticket followup answers")


def test_weak_reply():
    assert is_weak_ticket_reply("嗯", {}) is True
    assert is_weak_ticket_reply("随便", {}) is True
    slots = extract_ticket_slots("用来办签证", "certify")
    assert is_weak_ticket_reply("用来办签证", slots) is False
    print("[PASS] weak reply detection")


def test_modify_prompt_not_confirm_card():
    config = TICKET_SLOT_CONFIG["certify"]
    filled = {
        "purpose": "办签证",
        "receiver": "日本",
        "need_stamp": True,
        "expected_time": "这周五前",
    }
    prompt = build_ticket_modify_prompt(config, filled)
    assert "修改模式" in prompt
    assert "日本" in prompt
    assert "确认以下工单信息" not in prompt
    print("[PASS] modify prompt")


def test_slot_field_update():
    updates = extract_slot_field_updates("接收单位改成日本领事馆", "certify")
    assert updates.get("receiver") == "日本领事馆"
    print("[PASS] slot field update")


def test_certify_slot_extraction():
    text = "用来办签证，交给日本领事馆，要盖章，最好这周五前"
    slots = extract_ticket_slots(text, "certify")
    assert slots.get("purpose") == "办签证"
    assert slots.get("receiver") == "日本"
    assert slots.get("need_stamp") is True
    assert slots.get("expected_time")
    updates = extract_slot_field_updates(text, "certify")
    assert "receiver" not in updates
    print("[PASS] certify slot extraction:", slots)


def test_no_slot_update_on_initial_fill():
    text = "用来办签证，交给日本领事馆，要盖章，最好这周五前"
    assert should_extract_slot_updates(text) is False
    assert should_extract_slot_updates("接收单位改成日本领事馆") is True
    print("[PASS] should_extract_slot_updates")


def test_confirm_intent_phrases():
    assert is_ticket_confirm_intent("可以提交吧?", None) is True
    assert is_ticket_confirm_intent("没问题，提交吧", None) is True
    assert is_ticket_confirm_intent("这样可以吗?", None) is False
    print("[PASS] confirm intent phrases")


def test_validation_intent():
    assert is_ticket_validation_intent("这样可以吗?") is True
    assert is_ticket_validation_intent("信息填的对吗") is True
    assert is_ticket_info_query("刚才提交的这个工单的工单号是多少?") is True
    print("[PASS] validation and info query")


def test_validation_answer_complete():
    config = TICKET_SLOT_CONFIG["certify"]
    filled = {
        "purpose": "办签证",
        "receiver": "日本领事馆",
        "need_stamp": True,
        "expected_time": "这周五前",
    }
    ans = build_ticket_validation_answer(config, filled)
    assert "完整" in ans
    assert "办签证" in ans
    assert "确认提交" in ans
    print("[PASS] validation answer complete")


def test_general_qa_blocks_submit_phrases_in_certify():
    assert is_general_question_instead_of_ticket("可以提交吧?", "certify") is False
    assert is_general_question_instead_of_ticket("这样可以吗?", "certify") is False
    print("[PASS] submit/validation not treated as general QA")
    assert is_ticket_resume_intent("继续修改", "modify") is True
    assert is_ticket_resume_intent("继续修改", None) is True
    assert is_ticket_resume_intent("确认提交", "confirm_submit") is True
    print("[PASS] resume intent after pause")


def test_generic_new_ticket_intent():
    intent = detect_ticket_intent("提交一个新工单")
    assert intent["is_ticket_intent"] is True
    assert intent.get("needs_type_selection") is True
    assert is_generic_new_ticket_intent("提交一个新工单") is True
    assert parse_ticket_type_choice("我想再开一份在职证明") == "certify"
    assert parse_ticket_type_choice("1") == "certify"
    print("[PASS] generic new ticket intent")


if __name__ == "__main__":
    test_modify_intent_with_action()
    test_general_qa_exit_during_certify()
    test_ticket_flow_followup()
    test_ticket_followup_answers()
    test_weak_reply()
    test_modify_prompt_not_confirm_card()
    test_slot_field_update()
    test_certify_slot_extraction()
    test_no_slot_update_on_initial_fill()
    test_confirm_intent_phrases()
    test_validation_intent()
    test_validation_answer_complete()
    test_general_qa_blocks_submit_phrases_in_certify()
    test_generic_new_ticket_intent()
    print("ALL PASSED")
