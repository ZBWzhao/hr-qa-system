"""工单 type 字段：canonical 中文入库 + 展示标签"""

from collections import defaultdict

from app.services.ticket_intent_service import TICKET_SLOT_CONFIG

# 允许写入数据库的 canonical 中文类型（与智能问答 TICKET_SLOT_CONFIG 一致）
CANONICAL_TICKET_TYPES = frozenset(TICKET_SLOT_CONFIG.keys())

# 各类别名 / 英文 key → canonical 中文
TYPE_TO_CANONICAL: dict[str, str] = {
    "certify": "证明开具",
    "info_change": "信息变更",
    "attendance_exception": "考勤异常",
    "leave_request": "请假申请",
    "reimbursement": "报销薪资",
    "resignation": "离职申请",
    "probation": "入职转正",
    "other": "其他",
    "报销/薪资": "报销薪资",
    "入职/转正": "入职转正",
    "人工请求": "其他",
}

for _key, _cfg in TICKET_SLOT_CONFIG.items():
    TYPE_TO_CANONICAL[_key] = _key
    _display = _cfg.get("display_type")
    if _display:
        TYPE_TO_CANONICAL[_display] = _key

# 展示用标签（含英文兼容，供统计/图表合并）
TICKET_TYPE_LABELS: dict[str, str] = dict(TYPE_TO_CANONICAL)
for _key, _cfg in TICKET_SLOT_CONFIG.items():
    _label = _cfg.get("display_type") or _key
    TICKET_TYPE_LABELS[_key] = _label
    TICKET_TYPE_LABELS[_label] = _label
TICKET_TYPE_LABELS.update({
    "certify": "证明开具",
    "info_change": "信息变更",
    "attendance_exception": "考勤异常",
    "leave_request": "请假申请",
    "reimbursement": "报销/薪资",
    "resignation": "离职申请",
    "probation": "入职/转正",
    "other": "人工请求",
    "报销薪资": "报销/薪资",
    "入职转正": "入职/转正",
    "其他": "人工请求",
})


def normalize_ticket_type(ticket_type: str | None) -> str:
    """归一化为 canonical 中文类型，供数据库入库与筛选"""
    if not ticket_type:
        return "其他"
    key = str(ticket_type).strip()
    if key in TYPE_TO_CANONICAL:
        return TYPE_TO_CANONICAL[key]
    if key in CANONICAL_TICKET_TYPES:
        return key
    return "其他"


def get_ticket_type_display(ticket_type: str | None) -> str:
    """UI 展示名；未知类型不暴露英文 key"""
    canonical = normalize_ticket_type(ticket_type)
    cfg = TICKET_SLOT_CONFIG.get(canonical)
    if cfg:
        return cfg.get("display_type") or canonical
    return get_ticket_type_label(ticket_type)


def get_ticket_type_label(ticket_type: str | None) -> str:
    """将工单 type 转为中文展示名（兼容历史英文 key）"""
    if not ticket_type:
        return "其他"
    key = str(ticket_type).strip()
    if key in TICKET_TYPE_LABELS:
        return TICKET_TYPE_LABELS[key]
    if any("\u4e00" <= ch <= "\u9fff" for ch in key):
        return key
    return "其他"


def merge_ticket_type_rows(rows: list[tuple]) -> list[dict]:
    """按中文展示标签合并工单类型统计行"""
    merged: dict[str, int] = defaultdict(int)
    for ticket_type, count in rows:
        merged[get_ticket_type_label(ticket_type)] += int(count or 0)
    return [{"name": name, "value": value} for name, value in merged.items()]


def migrate_ticket_types_in_db(db) -> int:
    """将 biz_ticket.type 中的英文/别名统一为 canonical 中文（幂等）"""
    from sqlalchemy import text

    updated = 0
    rows = db.execute(text("SELECT id, type FROM biz_ticket")).fetchall()
    for ticket_id, raw_type in rows:
        canonical = normalize_ticket_type(raw_type)
        if raw_type != canonical:
            db.execute(
                text("UPDATE biz_ticket SET type = :canonical WHERE id = :id"),
                {"canonical": canonical, "id": ticket_id},
            )
            updated += 1
    if updated:
        db.commit()
    return updated
