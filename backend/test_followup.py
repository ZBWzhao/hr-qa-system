"""
追问场景回归测试
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.followup_service import (
    is_followup_question,
    build_no_context_clarification,
    rewrite_followup_question,
    get_recent_context,
    is_unresolved_followup,
    get_attendance_policy_answer,
    get_annual_leave_followup_answer,
    get_seniority_welfare_followup_answer,
    is_seniority_welfare_calculation_question,
    is_ambiguous_followup_without_keywords,
    was_followup_rewritten,
    _parse_years_expression,
    _chinese_to_number,
)


def test_is_followup_question():
    cases = [
        ("3 年呢？", True),
        ("16 年呢？", True),
        ("那这个呢？", True),
        ("工作满 3 年呢？", True),
        ("那 3 年呢？", True),
        ("那迟到呢？", True),
        ("这个需要提交说明吗？", True),
        ("工作文档可以用 AI 写吗？", False),
        ("忘记打卡怎么办？", False),
    ]
    print("=" * 60)
    print("test_is_followup_question")
    all_pass = True
    for q, expected in cases:
        result = is_followup_question(q)
        ok = result == expected
        all_pass = all_pass and ok
        print(f"  {'[PASS]' if ok else '[FAIL]'} {q!r} -> {result}")
    return all_pass


def test_no_context_clarification():
    msg = build_no_context_clarification("3 年呢？")
    assert "补充上下文" in msg
    assert "年假" in msg
    print("[PASS] build_no_context_clarification for 3 年呢？")


def test_rewrite_incompatible_year_after_faq():
    ctx = {
        "conversation_topic": "general",
        "last_topic": "general",
        "last_question": "工作文档可以用 AI 写吗？",
        "last_subtopic": "",
    }
    result = rewrite_followup_question("那 3 年呢？", ctx)
    assert result.get("need_clarification") is True
    assert "工龄" in result.get("clarification_message", "")
    print("[PASS] incompatible year after FAQ -> clarification")


def test_rewrite_attendance_late():
    ctx = {
        "conversation_topic": "attendance",
        "last_topic": "attendance",
        "last_question": "忘记打卡怎么办？",
        "last_subtopic": "忘记打卡",
    }
    result = rewrite_followup_question("那迟到呢？", ctx)
    assert result.get("resolved_question") == "迟到怎么处理？"
    print("[PASS] 那迟到呢？ -> 迟到怎么处理？")


def test_rewrite_pronoun_after_late():
    ctx = {
        "conversation_topic": "attendance",
        "last_topic": "attendance",
        "last_question": "那迟到呢？",
        "last_subtopic": "迟到",
    }
    result = rewrite_followup_question("这个需要提交说明吗？", ctx)
    assert result.get("resolved_question") == "迟到需要提交考勤异常说明吗？"
    print("[PASS] 这个需要提交说明吗？ -> 迟到需要提交考勤异常说明吗？")


def test_unresolved_followup():
    assert is_unresolved_followup("3 年呢？", False, {}) is True
    assert is_unresolved_followup(
        "那 3 年呢？",
        True,
        {"resolved_question": "那 3 年呢？", "inherited_topic": "general"},
    ) is True
    assert is_unresolved_followup(
        "那迟到呢？",
        True,
        {"resolved_question": "迟到怎么处理？", "inherited_topic": "attendance"},
    ) is False
    print("[PASS] is_unresolved_followup")


def test_standalone_expand_late():
    result = rewrite_followup_question("那迟到呢？", {
        "conversation_topic": "",
        "last_topic": "",
        "last_question": "",
        "last_subtopic": "",
        "has_history": False,
    })
    assert result.get("resolved_question") == "迟到怎么处理？"
    assert result.get("inherited_topic") == "attendance"
    assert result.get("standalone_expand") is True
    print("[PASS] standalone expand: 那迟到呢？")


def test_topic_from_clarification_record():
    """澄清回答模板含「年假」，但主题应从用户问题「那迟到呢？」推断为 attendance"""
    from app.models.qa import QARecord

    class FakeRecord:
        def __init__(self, question, answer, answer_type):
            self.question = question
            self.answer = answer
            self.answer_type = answer_type

    records = [
        FakeRecord(
            "那迟到呢？",
            "你这个问题需要结合上下文才能准确回答。\n\n1. 年假天数\n2. 考勤、迟到、补卡",
            "clarification",
        ),
    ]
    from app.services.followup_service import _infer_conversation_topic, _infer_subtopic_from_records

    topic = _infer_conversation_topic(records)
    assert topic == "attendance", f"expected attendance, got {topic}"
    sub = _infer_subtopic_from_records(records, topic)
    assert sub == "迟到"
    print("[PASS] topic inference skips clarification template pollution")


def test_pronoun_after_clarification_on_late():
    ctx = {
        "conversation_topic": "attendance",
        "last_topic": "attendance",
        "last_question": "那迟到呢？",
        "last_subtopic": "迟到",
        "last_answer_summary": "请补充你想了解的具体内容，例如考勤、迟到、补卡",
    }
    result = rewrite_followup_question("这个需要提交说明吗？", ctx)
    assert result.get("resolved_question") == "迟到需要提交考勤异常说明吗？"
    print("[PASS] pronoun after clarification on late topic")


def test_ambiguous_without_keywords():
    assert is_ambiguous_followup_without_keywords("3 年呢？") is True
    assert is_ambiguous_followup_without_keywords("那迟到呢？") is False
    print("[PASS] is_ambiguous_followup_without_keywords")


def test_chinese_years_parsing():
    assert _chinese_to_number("二十") == 20
    assert _chinese_to_number("三") == 3
    assert _parse_years_expression("二十年以上呢？") == (20, "以上")
    assert _parse_years_expression("如果我干了 3 年呢？") == (3, "")
    print("[PASS] chinese years parsing")


def test_year_followup_without_explicit_annual_leave():
    ctx = {
        "conversation_topic": "general",
        "last_topic": "general",
        "last_question": "3 年呢？",
        "last_subtopic": "",
        "last_answer_summary": "你是想问年假天数、工龄福利...",
        "recent_user_questions": ["3 年呢？"],
        "explicit_annual_leave_intent": False,
        "has_recent_year_followup": True,
    }
    result = rewrite_followup_question("16 年呢？", ctx)
    assert result.get("need_clarification") is True
    assert "补充上下文" in result.get("clarification_message", "")
    print("[PASS] 16 年呢？ without explicit 年假 -> clarification")


def test_year_followup_work_full_without_explicit():
    ctx = {
        "conversation_topic": "general",
        "recent_user_questions": ["3 年呢？", "16 年呢？"],
        "explicit_annual_leave_intent": False,
    }
    result = rewrite_followup_question("工作满 3 年呢？", ctx)
    assert result.get("need_clarification") is True
    assert "转正" in result.get("clarification_message", "") or "年假" in result.get("clarification_message", "")
    print("[PASS] 工作满 3 年呢？ without explicit -> clarification")


def test_pronoun_after_year_clarification():
    ctx = {
        "conversation_topic": "general",
        "last_question": "16 年呢？",
        "recent_user_questions": ["3 年呢？", "16 年呢？"],
        "explicit_annual_leave_intent": False,
        "has_recent_year_followup": True,
    }
    result = rewrite_followup_question("那这个呢？", ctx)
    assert result.get("need_clarification") is True
    assert "补充上下文" in result.get("clarification_message", "")
    print("[PASS] 那这个呢？ after year followups -> clarification")


def test_year_followup_with_explicit_annual_leave():
    ctx = {
        "conversation_topic": "annual_leave",
        "last_question": "公司年假是按什么标准算的？",
        "recent_user_questions": ["公司年假是按什么标准算的？", "如果我干了 3 年呢？"],
        "explicit_annual_leave_intent": True,
    }
    result = rewrite_followup_question("二十年以上呢？", ctx)
    assert result.get("resolved_question") == "工作年限20年以上有几天年假？"
    assert result.get("explicit_annual_leave_intent") is True
    print("[PASS] 二十年以上呢？ with explicit 年假 context -> rewrite")


def test_rewrite_chinese_years_annual_leave():
    ctx = {
        "conversation_topic": "annual_leave",
        "last_topic": "annual_leave",
        "last_question": "公司年假是按什么标准算的？",
        "last_subtopic": "",
        "last_answer_summary": "工龄满20年以上15天。",
        "recent_user_questions": ["公司年假是按什么标准算的？", "如果我干了 3 年呢？"],
        "explicit_annual_leave_intent": True,
    }
    result = rewrite_followup_question("二十年以上呢？", ctx)
    assert result.get("resolved_question") == "工作年限20年以上有几天年假？"
    assert result.get("inherited_topic") == "annual_leave"
    print("[PASS] 二十年以上呢？ with explicit intent -> rewrite")


def test_annual_leave_followup_answer_20_plus():
    policy = get_annual_leave_followup_answer("工作年限20年以上有几天年假？")
    assert policy.get("answer")
    assert "15" in policy["answer"]
    print("[PASS] 20年以上 -> 15天年假")


def test_attendance_policy_answer():
    policy = get_attendance_policy_answer("迟到需要提交考勤异常说明吗？")
    assert policy.get("answer")
    assert "30分钟" in policy["answer"]
    assert "考勤异常说明" in policy["answer"]
    print("[PASS] get_attendance_policy_answer")


def test_rewrite_pronoun_with_rag_context():
    ctx = {
        "conversation_topic": "attendance",
        "last_topic": "attendance",
        "last_question": "那迟到呢？",
        "last_subtopic": "迟到",
        "last_answer_summary": "迟到或早退30分钟以内，每次扣减当月绩效分1分。",
    }
    result = rewrite_followup_question("这个需要提交说明吗？", ctx)
    assert result.get("resolved_question") == "迟到需要提交考勤异常说明吗？"
    print("[PASS] pronoun followup with RAG context")


def test_seniority_welfare_calculation_15_years():
    q = "是这样的, 我现在积累工作了15年, 公司有没有规定有什么福利"
    assert is_seniority_welfare_calculation_question(q) is True
    policy = get_seniority_welfare_followup_answer(q)
    assert policy.get("answer")
    assert "5000" in policy["answer"]
    assert "5 个3年周期" in policy["answer"] or "5个3年周期" in policy["answer"]
    print("[PASS] 15年工龄福利 -> 5000元")


def test_seniority_welfare_calculation_3_years():
    q = "工作3年有什么工龄福利？"
    assert is_seniority_welfare_calculation_question(q) is True
    policy = get_seniority_welfare_followup_answer(q)
    assert "1000" in policy["answer"]
    print("[PASS] 3年工龄福利 -> 1000元")


def test_rewrite_salary_welfare_with_years():
    ctx = {
        "conversation_topic": "salary_welfare",
        "last_topic": "salary_welfare",
        "last_question": "工龄福利",
        "recent_user_questions": ["那 3 年呢？", "工龄福利"],
    }
    q = "是这样的, 我现在积累工作了15年, 公司有没有规定有什么福利"
    result = rewrite_followup_question(q, ctx)
    assert result.get("inherited_topic") == "salary_welfare"
    assert "15年" in result.get("resolved_question", "")
    print("[PASS] salary_welfare followup with 15 years rewrite")


if __name__ == "__main__":
    ok = test_is_followup_question()
    test_no_context_clarification()
    test_rewrite_incompatible_year_after_faq()
    test_rewrite_attendance_late()
    test_standalone_expand_late()
    test_topic_from_clarification_record()
    test_pronoun_after_clarification_on_late()
    test_ambiguous_without_keywords()
    test_chinese_years_parsing()
    test_year_followup_without_explicit_annual_leave()
    test_year_followup_work_full_without_explicit()
    test_pronoun_after_year_clarification()
    test_year_followup_with_explicit_annual_leave()
    test_rewrite_chinese_years_annual_leave()
    test_annual_leave_followup_answer_20_plus()
    test_rewrite_pronoun_after_late()
    test_rewrite_pronoun_with_rag_context()
    test_attendance_policy_answer()
    test_unresolved_followup()
    test_seniority_welfare_calculation_15_years()
    test_seniority_welfare_calculation_3_years()
    test_rewrite_salary_welfare_with_years()
    print("=" * 60)
    print("ALL PASSED" if ok else "SOME FAILED")
