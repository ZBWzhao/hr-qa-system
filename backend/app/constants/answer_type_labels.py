"""问答 answer_type 统一中文标签"""

ANSWER_TYPE_LABELS: dict[str, str] = {
    "faq": "标准答案",
    "rule": "规则匹配",
    "rag": "文档检索",
    "miss": "未命中",
    "clarification": "澄清追问",
    "followup_clarification": "追问澄清",
    "followup_no_context": "追问澄清",
    "ticket_form": "工单申请",
    "ticket_clarification": "工单申请",
    "ticket_qa": "工单咨询",
    "ticket_confirm": "工单确认",
    "ticket_submitted": "工单已提交",
    "notice_form": "公告发布",
    "notice_clarification": "公告发布",
    "notice_confirm": "公告确认",
    "notice_published": "公告已发布",
    "no_permission": "无权限",
    "system": "系统消息",
    "mock": "模拟问答",
    "error": "系统异常",
}


def get_answer_type_label(answer_type: str | None) -> str:
    """将 answer_type 转为中文展示名；未知类型返回「其他」，不暴露英文 key"""
    if not answer_type:
        return "其他"
    key = str(answer_type).strip()
    if key in ANSWER_TYPE_LABELS:
        return ANSWER_TYPE_LABELS[key]
    if key.startswith("notice_"):
        return "公告相关"
    if key.startswith("ticket_"):
        return "工单相关"
    return "其他"
