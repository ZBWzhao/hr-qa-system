"""AI 增强回答回归测试"""
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm import is_ai_service_error, generate_knowledge_answer
from app.api.chat import _ai_enhance_answer


def test_is_ai_service_error():
    assert is_ai_service_error("") is True
    assert is_ai_service_error("AI服务错误: timeout") is True
    assert is_ai_service_error("HR电话是010-88888888") is False
    print("[PASS] is_ai_service_error")


def test_ai_enhance_fallback_on_error():
    knowledge = (
        "规则名称：HR联系方式查询\n"
        "规定内容：\n电话：010-88888888\n邮箱：hr@company.com"
    )
    with patch("app.api.chat.generate_knowledge_answer", return_value="AI服务响应超时，请稍后重试"):
        answer = _ai_enhance_answer(
            question="HR 电话是多少？",
            knowledge=knowledge,
            source_label="公司规则",
            fallback="电话：010-88888888",
        )
    assert answer == "电话：010-88888888"
    print("[PASS] ai enhance fallback on API error")


def test_ai_enhance_uses_llm_output():
    knowledge = "标准答案：每工作3年, 年终奖额外增加1000元."
    with patch("app.api.chat.generate_knowledge_answer", return_value="工作满3年，年终奖会额外增加1000元。"):
        answer = _ai_enhance_answer(
            question="3年有什么福利？",
            knowledge=knowledge,
            source_label="标准FAQ",
            fallback=knowledge,
        )
    assert "1000" in answer
    assert "AI服务" not in answer
    print("[PASS] ai enhance uses LLM output")


if __name__ == "__main__":
    test_is_ai_service_error()
    test_ai_enhance_fallback_on_error()
    test_ai_enhance_uses_llm_output()
    print("ALL PASSED")
