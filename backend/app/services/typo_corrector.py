"""静默错别字/拼音纠错：优先 AI 理解意图，失败时回退原文"""
import re

from app.services.llm import correct_user_question_typos, is_ai_service_error

_PINYIN_DATE = re.compile(r"(\d+)\s*yue\s*(\d+)\s*日?", re.IGNORECASE)


def _fix_pinyin_dates(text: str) -> str:
    result = _PINYIN_DATE.sub(r"\1月\2日", text)
    result = re.sub(
        r"(\d+)\s*yue\s*(\d+)(?![\d月日])",
        r"\1月\2日",
        result,
        flags=re.IGNORECASE,
    )
    return result


def _likely_needs_ai_correction(text: str) -> bool:
    """长度足够的用户输入均走 AI 意图理解纠错（极短输入跳过）"""
    return len(text.strip()) >= 4


def normalize_question_typos(text: str) -> str:
    if not text or not str(text).strip():
        return text

    original = str(text).strip()
    preprocessed = _fix_pinyin_dates(original)

    if not _likely_needs_ai_correction(preprocessed):
        return preprocessed

    corrected = correct_user_question_typos(preprocessed)
    if corrected and not is_ai_service_error(corrected):
        cleaned = corrected.strip().strip("「」\"'""")
        if cleaned and len(cleaned) <= max(len(preprocessed) * 2, len(preprocessed) + 80):
            return cleaned

    return preprocessed
