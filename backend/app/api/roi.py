from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models.qa import QARecord
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter()


@router.get("")
def get_roi_report(current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    now = datetime.now()
    month_ago = now - timedelta(days=30)

    total_qa = db.query(QARecord).count()
    month_qa = db.query(QARecord).filter(QARecord.created_at >= month_ago).count()
    total_tickets = db.query(Ticket).count()
    month_tickets = db.query(Ticket).filter(Ticket.created_at >= month_ago).count()

    avg_time_per_question = 5
    saved_hours = round(total_qa * avg_time_per_question / 60, 1)
    month_saved_hours = round(month_qa * avg_time_per_question / 60, 1)

    daily_qa = db.query(func.date(QARecord.created_at), func.count()).filter(QARecord.created_at >= month_ago).group_by(func.date(QARecord.created_at)).all()
    trend = [{"date": str(d[0]), "count": d[1]} for d in daily_qa]

    return success({
        "total_qa": total_qa,
        "month_qa": month_qa,
        "total_tickets": total_tickets,
        "month_tickets": month_tickets,
        "total_saved_hours": saved_hours,
        "month_saved_hours": month_saved_hours,
        "equivalent_fte": round(month_saved_hours / 160, 2),
        "qa_trend": trend,
        "roi_percentage": round((month_saved_hours * 100) / (160 * 2), 1) if month_saved_hours > 0 else 0,
        "report_summary": f"本月智能问答{month_qa}次，等效节省{month_saved_hours}工时，相当于{round(month_saved_hours/160, 1)}个全职HR的工作量"
    })
