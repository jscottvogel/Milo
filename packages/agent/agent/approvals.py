import datetime
import uuid
from typing import Any

from sqlalchemy.orm import Session

from db.models.agent import Approval


def create_approval(
    session: Session,
    tenant_id: str,
    milo_id: str,
    thread_id: str,
    tool_name: str,
    payload: dict[str, Any],
    expires_in_hours: int = 24
) -> Approval:
    """Create a new approval request in the database."""
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expires_in_hours)
    
    approval = Approval(
        tenant_id=uuid.UUID(tenant_id),
        milo_id=uuid.UUID(milo_id),
        thread_id=uuid.UUID(thread_id),
        tool_name=tool_name,
        payload_jsonb=payload,
        status="pending",
        expires_at=expires_at
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)
    return approval


def decide_approval(
    session: Session,
    tenant_id: str,
    approval_id: str,
    decision: str,
    user_id: str,
    modified_payload: dict[str, Any] | None = None
) -> Approval:
    """Decide on an approval (approved, rejected)."""
    approval = session.get(Approval, uuid.UUID(approval_id))
    if not approval or str(approval.tenant_id) != tenant_id:
        raise ValueError("Approval not found")
        
    if approval.status != "pending":
        raise ValueError(f"Approval is already {approval.status}")
        
    if decision not in ["approved", "rejected"]:
        raise ValueError("Decision must be 'approved' or 'rejected'")
        
    approval.status = decision
    approval.decided_by = uuid.UUID(user_id)
    approval.decided_at = datetime.datetime.now(datetime.UTC)
    
    if modified_payload and decision == "approved":
        approval.payload_jsonb = modified_payload
        
    session.commit()
    session.refresh(approval)
    return approval
