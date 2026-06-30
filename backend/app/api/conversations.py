from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success, error
from app.models.qa import QARecord
from app.models.user import User
from app.schemas.qa import ConversationItem, ConversationGroup

router = APIRouter()

GROUP_ORDER = ["today", "yesterday", "last_7_days", "last_30_days", "earlier"]


def _classify_date_group(dt: datetime) -> str:
    now = datetime.now()
    today = now.date()
    delta = today - dt.date()
    if delta.days == 0:
        return "today"
    elif delta.days == 1:
        return "yesterday"
    elif delta.days <= 7:
        return "last_7_days"
    elif delta.days <= 30:
        return "last_30_days"
    return "earlier"


@router.get("")
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(QARecord).filter(
        QARecord.user_id == current_user.id,
        QARecord.conversation_id.isnot(None)
    ).order_by(QARecord.created_at.asc()).all()

    conv_map: dict[str, list[QARecord]] = {}
    for r in records:
        conv_map.setdefault(r.conversation_id, []).append(r)

    conversations = []
    for cid, recs in conv_map.items():
        conversations.append(ConversationItem(
            conversation_id=cid,
            title=recs[0].question[:50],
            last_message=recs[-1].answer[:50],
            message_count=len(recs),
            created_at=recs[0].created_at,
            updated_at=recs[-1].created_at,
        ))

    conversations.sort(key=lambda c: c.updated_at, reverse=True)

    groups_dict: dict[str, list[ConversationItem]] = {}
    for conv in conversations:
        label = _classify_date_group(conv.updated_at)
        groups_dict.setdefault(label, []).append(conv)

    groups = []
    for label in GROUP_ORDER:
        if label in groups_dict:
            groups.append(ConversationGroup(label=label, conversations=groups_dict[label]))

    return success({"groups": [g.model_dump() for g in groups]})


@router.get("/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(QARecord).filter(
        QARecord.user_id == current_user.id,
        QARecord.conversation_id == conversation_id
    ).order_by(QARecord.created_at.asc()).all()

    if not records:
        return error("对话不存在", code=404)

    messages = []
    for r in records:
        messages.append({
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "answer_type": r.answer_type,
            "source_docs": r.source_docs,
            "feedback": r.feedback,
            "is_favorite": r.is_favorite,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return success({"conversation_id": conversation_id, "messages": messages})


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(QARecord).filter(
        QARecord.user_id == current_user.id,
        QARecord.conversation_id == conversation_id
    ).delete()

    if count == 0:
        return error("对话不存在", code=404)

    db.commit()
    return success(None, "对话已删除")
