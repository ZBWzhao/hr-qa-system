"""FAQ 匹配回归测试"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.followup_service import expand_clarification_choice


class FakeFAQ:
    def __init__(self, id, question, answer, keywords):
        self.id = id
        self.question = question
        self.answer = answer
        self.keywords = keywords
        self.status = 1
        self.view_count = 0


def test_expand_clarification_choice_gongling():
    ctx = {
        "last_answer_type": "clarification",
        "recent_user_questions": ["那 3 年呢？", "工龄福利"],
    }
    result = expand_clarification_choice("工龄福利", ctx)
    assert "工龄福利" in result.get("resolved_question", "")
    assert result.get("inherited_topic") == "salary_welfare"
    print("[PASS] expand 工龄福利 with 3年 context")


def test_match_faq_welfare_not_ai_doc():
    from unittest.mock import MagicMock
    from app.api.chat import match_faq

    faqs = [
        FakeFAQ(8, "工作文档可以用AI写吗?", "可以,但是查重率不能超过70%", "AI,文档,写作"),
        FakeFAQ(9, "关于工龄福利方面", "每工作3年, 年终奖额外增加1000元.", "工龄,福利,年终奖"),
    ]

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = faqs

    q = "是这样的, 我现在积累工作了15年, 公司有没有规定有什么福利"
    matched = match_faq(mock_db, q, conversation_topic="salary_welfare")
    assert matched is not None
    assert matched.id == 9, f"expected FAQ #9, got {matched.id if matched else None}"
    print("[PASS] welfare question matches 工龄福利 FAQ not 工作文档")


if __name__ == "__main__":
    test_expand_clarification_choice_gongling()
    test_match_faq_welfare_not_ai_doc()
    print("ALL PASSED")
