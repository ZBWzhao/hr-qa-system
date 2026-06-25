from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models.qa import FAQ, QARecord
from app.models.user import User

router = APIRouter()


@router.get("")
def get_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hot_faqs = db.query(FAQ).filter(FAQ.status == 1).order_by(FAQ.view_count.desc()).limit(5).all()
    user_questions = db.query(QARecord).filter(QARecord.user_id == current_user.id).order_by(QARecord.created_at.desc()).limit(3).all()

    recommendations = []
    for faq in hot_faqs:
        recommendations.append({"type": "faq", "question": faq.question, "faq_id": faq.id})

    default_questions = [
        "年假怎么计算？",
        "请假需要提前多久申请？",
        "报销流程是什么？",
        "试用期多久？",
        "绩效申诉怎么提交？"
    ]
    existing = set(r["question"] for r in recommendations)
    for q in default_questions:
        if q not in existing and len(recommendations) < 8:
            recommendations.append({"type": "default", "question": q})
            existing.add(q)

    return success(recommendations)
