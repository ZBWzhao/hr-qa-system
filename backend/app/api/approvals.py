import uuid
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.core.response import success
from app.models.user import User

router = APIRouter()

mock_approvals = {}


@router.post("/initiate")
def initiate_approval(title: str = "审批申请", current_user: User = Depends(get_current_user)):
    approval_id = str(uuid.uuid4())[:8]
    mock_approvals[approval_id] = {
        "id": approval_id,
        "title": title,
        "applicant": current_user.real_name,
        "status": "pending",
        "steps": [
            {"name": "部门主管审批", "status": "pending"},
            {"name": "HR审批", "status": "pending"},
            {"name": "总经理审批", "status": "pending"}
        ]
    }
    return success(mock_approvals[approval_id])


@router.get("/status")
def get_approval_status(approval_id: str):
    if approval_id in mock_approvals:
        return success(mock_approvals[approval_id])
    return success({
        "id": approval_id,
        "status": "pending",
        "steps": [
            {"name": "部门主管审批", "status": "approved"},
            {"name": "HR审批", "status": "pending"},
            {"name": "总经理审批", "status": "pending"}
        ]
    })
