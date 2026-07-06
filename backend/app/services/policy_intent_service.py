"""区分「制度/政策咨询」与「办理工单」意图"""
import re

# 询问制度细节的信号
POLICY_CONSULTATION_SIGNALS = (
    "流程是什么",
    "流程是怎样的",
    "流程有哪些",
    "有哪些流程",
    "讲解",
    "解读",
    "解释",
    "说明",
    "什么意思",
    "是什么",
    "规定",
    "制度",
    "办法",
    "要求",
    "条件",
    "标准",
    "需要什么",
    "有哪些",
    "怎么办",
    "怎么做",
    "如何",
    "怎么",
    "了解一下",
    "想了解",
    "想知道",
    "介绍",
    "讲讲",
    "告诉我",
    "用人话",
    "通俗",
    "白话",
)

# 明确要提交/办理工单的信号
TICKET_SUBMISSION_SIGNALS = (
    "申请",
    "办理",
    "提交",
    "开具",
    "开证明",
    "帮我办",
    "我要办",
    "帮我请",
    "我要请",
    "帮我提交",
    "我要提交",
    "发起",
    "转人工",
    "人工处理",
    "新建工单",
    "创建工单",
    "提交工单",
    "申请工单",
)


def is_policy_consultation(question: str) -> bool:
    """用户是在问制度/流程/规定，而非要创建工单"""
    q = (question or "").strip()
    if not q:
        return False

    if any(s in q for s in TICKET_SUBMISSION_SIGNALS):
        return False

    if any(s in q for s in POLICY_CONSULTATION_SIGNALS):
        return True

    if re.search(r"(了解|咨询|询问|问|查).{0,8}(流程|规定|制度|手续|材料|条件)", q):
        return True

    if re.search(r"(流程|规定|制度|手续).{0,8}(是什么|有哪些|怎么样|怎样)", q):
        return True

    if re.search(r"了解.{0,6}(详细|流程|步骤|手续)", q):
        return True

    return False


def is_ticket_submission_request(question: str) -> bool:
    """用户明确要办理/提交工单"""
    q = (question or "").strip()
    return any(s in q for s in TICKET_SUBMISSION_SIGNALS)
