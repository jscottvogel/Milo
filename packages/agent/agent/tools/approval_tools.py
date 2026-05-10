from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ApprovalCreateInput(BaseModel):
    title: str = Field(description="Short description of what needs approval")
    description: str = Field(description="Full context, background, and recommendation")
    options: List[str] = Field(default=["approve", "reject", "delegate", "defer"], description="List of options")
    requested_by: str = Field(description="Milo or agent name")
    notify_email: str = Field(description="Email to notify")
    due_by: str = Field(description="ISO 8601 datetime — when decision is needed by")
    work_item_id: Optional[str] = Field(None, description="Linked work item UUID")
    metadata_: Optional[dict] = Field(None, alias="metadata", description="Any extra context")

class ApprovalCreateTool:
    name = "approval__create"
    description = "Request structured approval from a human for an action."
    input_schema = ApprovalCreateInput
    output_schema = None
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: Any) -> Any:
        import uuid
        from db.models.agent import ApprovalRequest
        
        parsed_input = ApprovalCreateInput(**input_data)
        
        req = ApprovalRequest(
            tenant_id=uuid.UUID(context.tenant_id),
            milo_id=uuid.UUID(context.milo_id),
            thread_id=uuid.UUID(context.thread_id),
            title=parsed_input.title,
            description=parsed_input.description,
            options_jsonb=parsed_input.options,
            context_payload_jsonb=parsed_input.metadata_ or {},
            urgency="medium",
            status="pending"
        )
        context.session.add(req)
        context.session.commit()
        context.session.refresh(req)
        
        # In a real implementation we'd also notify the human via email or socket
        
        return {
            "status": "interrupt_requested",
            "approval_id": str(req.id),
            "created_at": datetime.now().isoformat()
        }

class ApprovalReadInput(BaseModel):
    approval_id: Optional[str] = Field(None, description="Optional UUID to return single approval. Omit for all pending.")

class ApprovalReadTool:
    name = "approval__read"
    description = "Read the status of one or all pending approvals."
    input_schema = ApprovalReadInput
    output_schema = None
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: Any) -> Any:
        import uuid
        from db.models.agent import ApprovalRequest
        from sqlalchemy import select
        
        parsed_input = ApprovalReadInput(**input_data)
        
        stmt = select(ApprovalRequest).where(ApprovalRequest.tenant_id == uuid.UUID(context.tenant_id))
        if parsed_input.approval_id:
            stmt = stmt.where(ApprovalRequest.id == uuid.UUID(parsed_input.approval_id))
        else:
            stmt = stmt.where(ApprovalRequest.status == "pending")
            
        records = context.session.scalars(stmt).all()
        
        return {
            "approvals": [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                } for r in records
            ]
        }

class ApprovalRespondInput(BaseModel):
    approval_id: str = Field(description="The UUID of the approval")
    decision: str = Field(description="approved | rejected | delegated | deferred")
    notes: Optional[str] = Field(None, description="Reason or instructions")
    decided_by: str = Field(description="Name or email of decision maker")

class ApprovalRespondTool:
    name = "approval__respond"
    description = "Submit a decision on a pending approval."
    input_schema = ApprovalRespondInput
    output_schema = None
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: Any) -> Any:
        import uuid
        from db.models.agent import ApprovalRequest
        
        parsed_input = ApprovalRespondInput(**input_data)
        req = context.session.get(ApprovalRequest, uuid.UUID(parsed_input.approval_id))
        
        if not req or str(req.tenant_id) != context.tenant_id:
            return {"error": "Approval request not found"}
            
        req.status = parsed_input.decision
        req.response_notes = parsed_input.notes
        req.resolved_at = datetime.now()
        context.session.commit()
        
        return {
            "approval_id": parsed_input.approval_id,
            "status": req.status,
            "decided_at": req.resolved_at.isoformat()
        }

class ApprovalCancelInput(BaseModel):
    approval_id: str = Field(description="The UUID of the approval")
    reason: Optional[str] = Field(None, description="Optional reason for cancellation")

class ApprovalCancelTool:
    name = "approval__cancel"
    description = "Cancel a pending approval request."
    input_schema = ApprovalCancelInput
    output_schema = None
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: Any) -> Any:
        import uuid
        from db.models.agent import ApprovalRequest
        
        parsed_input = ApprovalCancelInput(**input_data)
        req = context.session.get(ApprovalRequest, uuid.UUID(parsed_input.approval_id))
        
        if not req or str(req.tenant_id) != context.tenant_id:
            return {"error": "Approval request not found"}
            
        req.status = "cancelled"
        req.response_notes = parsed_input.reason
        req.resolved_at = datetime.now()
        context.session.commit()
        
        return {
            "approval_id": parsed_input.approval_id,
            "status": "cancelled"
        }
