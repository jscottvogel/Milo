import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from agent.approvals import decide_approval
from db.models.agent import Approval
from db.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from schemas.approvals import ApprovalDecisionRequest, ApprovalResponse


router = APIRouter(prefix="/v1/approvals", tags=["approvals"])

# Mock dependencies for tenant/user isolation
def get_current_tenant_id() -> str:
    return "00000000-0000-0000-0000-000000000001"  # Replace with real auth

def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"  # Replace with real auth


@router.get("", response_model=list[ApprovalResponse])
def list_approvals(
    milo_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    stmt = select(Approval).where(Approval.tenant_id == uuid.UUID(tenant_id))
    
    if milo_id:
        stmt = stmt.where(Approval.milo_id == uuid.UUID(milo_id))
    if status:
        stmt = stmt.where(Approval.status == status)
        
    approvals = db.scalars(stmt).all()
    
    return [
        ApprovalResponse(
            id=str(a.id),
            milo_id=str(a.milo_id),
            thread_id=str(a.thread_id),
            tool_name=a.tool_name,
            payload=a.payload_jsonb,
            status=a.status,
            expires_at=a.expires_at,
            decided_by=str(a.decided_by) if a.decided_by else None,
            decided_at=a.decided_at
        ) for a in approvals
    ]


@router.post("/{approval_id}/decide", response_model=ApprovalResponse)
def decide_on_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id)
):
    try:
        approval = decide_approval(
            session=db,
            tenant_id=tenant_id,
            approval_id=approval_id,
            decision=request.decision,
            user_id=user_id,
            modified_payload=request.modified_payload
        )
        
        # After deciding, the frontend should prompt the agent to resume execution
        # In a fully event-driven system, this might emit an event to unpause the agent
        
        return ApprovalResponse(
            id=str(approval.id),
            milo_id=str(approval.milo_id),
            thread_id=str(approval.thread_id),
            tool_name=approval.tool_name,
            payload=approval.payload_jsonb,
            status=approval.status,
            expires_at=approval.expires_at,
            decided_by=str(approval.decided_by) if approval.decided_by else None,
            decided_at=approval.decided_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
