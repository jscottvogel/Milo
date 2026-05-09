import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import Approval
from .notifier import send_approval_email
from .email_parser import parse_inbound_email

router = APIRouter(prefix="/approvals", tags=["approvals"])

# --- Schemas ---
class ApprovalCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    options: List[str] = Field(default=["approve", "reject"])
    requested_by: str
    notify_email: str
    due_by: Optional[datetime] = None
    work_item_id: Optional[str] = None
    metadata_: Optional[dict] = Field(None, alias="metadata")

class ApprovalResponse(BaseModel):
    id: str
    title: str
    status: str
    decision: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    due_by: Optional[datetime] = None
    work_item_id: Optional[str] = None

class ApprovalRespondRequest(BaseModel):
    decision: str
    notes: Optional[str] = None
    decided_by: str

class ApprovalCancelRequest(BaseModel):
    reason: Optional[str] = None

# --- Dependencies (Mocks for standalone service) ---
def get_db(request: Request):
    db = getattr(request.state, "db", None)
    if not db:
        # Fallback for standalone testing
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        from .models import Base
        Base.metadata.create_all(bind=engine)
    try:
        yield db
    finally:
        db.close()

def get_tenant_id(request: Request) -> uuid.UUID:
    context = getattr(request.state, "auth_context", None)
    if context:
        return uuid.UUID(context.tenant_id)
    # Fallback for local testing
    return uuid.uuid4()

# --- Endpoints ---

@router.post("", response_model=dict)
async def create_approval(
    payload: ApprovalCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    tenant_id = get_tenant_id(request)
    
    approval = Approval(
        tenant_id=tenant_id,
        title=payload.title,
        description=payload.description,
        options=payload.options,
        requested_by=payload.requested_by,
        notify_email=payload.notify_email,
        due_by=payload.due_by,
        work_item_id=uuid.UUID(payload.work_item_id) if payload.work_item_id else None,
        metadata_=payload.metadata_
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    # Send email notification
    background_tasks.add_task(send_approval_email, approval)
    
    return {
        "approval_id": str(approval.id),
        "status": approval.status,
        "created_at": approval.created_at.isoformat() if approval.created_at else None
    }

@router.get("", response_model=dict)
def list_approvals(
    request: Request,
    approval_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    tenant_id = get_tenant_id(request)
    
    stmt = select(Approval).where(Approval.tenant_id == tenant_id)
    if approval_id:
        stmt = stmt.where(Approval.id == uuid.UUID(approval_id))
        
    approvals = db.scalars(stmt).all()
    
    # Auto-expire logic check
    now = datetime.now(timezone.utc)
    updated = False
    for a in approvals:
        if a.status == "pending" and a.due_by and a.due_by < now:
            a.status = "expired"
            updated = True
            # In a full system, we would trigger `trigger__evaluate` here
    if updated:
        db.commit()
        
    result = []
    for a in approvals:
        result.append(ApprovalResponse(
            id=str(a.id),
            title=a.title,
            status=a.status,
            decision=a.decision,
            decided_by=a.decided_by,
            decided_at=a.decided_at,
            due_by=a.due_by,
            work_item_id=str(a.work_item_id) if a.work_item_id else None
        ).model_dump())
        
    return {"approvals": result}

@router.get("/{id}", response_model=dict)
def get_approval(
    id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    tenant_id = get_tenant_id(request)
    approval = db.query(Approval).filter(Approval.id == uuid.UUID(id), Approval.tenant_id == tenant_id).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    return {"approvals": [ApprovalResponse(
        id=str(approval.id),
        title=approval.title,
        status=approval.status,
        decision=approval.decision,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
        due_by=approval.due_by,
        work_item_id=str(approval.work_item_id) if approval.work_item_id else None
    ).model_dump()]}

@router.post("/{id}/respond", response_model=dict)
def respond_approval(
    id: str,
    payload: ApprovalRespondRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    tenant_id = get_tenant_id(request)
    approval = db.query(Approval).filter(Approval.id == uuid.UUID(id), Approval.tenant_id == tenant_id).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval is not pending")
        
    if payload.decision not in approval.options:
        raise HTTPException(status_code=400, detail="Invalid decision")
        
    approval.decision = payload.decision
    approval.status = payload.decision
    if payload.decision == "approve":
        approval.status = "approved"
    elif payload.decision == "reject":
        approval.status = "rejected"
    elif payload.decision == "delegate":
        approval.status = "delegated"
    elif payload.decision == "defer":
        approval.status = "deferred"
        
    approval.decided_by = payload.decided_by
    approval.decided_at = datetime.now(timezone.utc)
    if payload.notes:
        approval.notes = payload.notes
        
    db.commit()
    
    return {
        "approval_id": str(approval.id),
        "status": approval.status,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None
    }

@router.delete("/{id}", response_model=dict)
def cancel_approval(
    id: str,
    payload: Optional[ApprovalCancelRequest],
    request: Request,
    db: Session = Depends(get_db)
):
    tenant_id = get_tenant_id(request)
    approval = db.query(Approval).filter(Approval.id == uuid.UUID(id), Approval.tenant_id == tenant_id).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending approvals")
        
    approval.status = "cancelled"
    if payload and payload.reason:
        approval.notes = f"Cancelled: {payload.reason}"
        
    db.commit()
    
    return {
        "approval_id": str(approval.id),
        "status": approval.status
    }

@router.post("/inbound-email")
def inbound_email_webhook(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """Webhook for Nylas reply parser."""
    # Note: Tenant ID extraction might be complex here depending on Nylas webhook structure,
    # often it requires looking up the grant_id or account_id from the payload.
    # For now, we pass it to the parser.
    parse_inbound_email(payload, db)
    return {"status": "ok"}
