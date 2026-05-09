from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Assuming standard langchain_core tools import
def tool(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

# --- approval__create ---
class ApprovalCreateInput(BaseModel):
    title: str = Field(description="Short description of what needs approval")
    description: str = Field(description="Full context, background, and recommendation")
    options: List[str] = Field(default=["approve", "reject", "delegate", "defer"], description="List of options")
    requested_by: str = Field(description="Milo or agent name")
    notify_email: str = Field(description="Email to notify")
    due_by: str = Field(description="ISO 8601 datetime — when decision is needed by")
    work_item_id: Optional[str] = Field(None, description="Linked work item UUID")
    metadata_: Optional[dict] = Field(None, alias="metadata", description="Any extra context")

@tool("approval__create")
async def approval__create(input_data: ApprovalCreateInput, context: Any = None) -> dict:
    """
    Queue a structured approval request and send notification.
    Returns approval_id, status, and created_at.
    """
    # In a full implementation, this makes a POST request to /services/approvals (or local router)
    import httpx
    # local or service URL
    url = "http://localhost:8000/approvals"
    
    payload = input_data.model_dump(by_alias=True)
    # Mocking actual call for stub
    # async with httpx.AsyncClient() as client:
    #     resp = await client.post(url, json=payload)
    #     return resp.json()
    
    return {
        "approval_id": "dummy-uuid",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

# --- approval__read ---
class ApprovalReadInput(BaseModel):
    approval_id: Optional[str] = Field(None, description="Optional UUID to return single approval. Omit for all pending.")

@tool("approval__read")
async def approval__read(input_data: ApprovalReadInput, context: Any = None) -> dict:
    """
    Read the status of one or all pending approvals.
    Returns a list of approval records.
    """
    return {
        "approvals": []
    }

# --- approval__respond ---
class ApprovalRespondInput(BaseModel):
    approval_id: str = Field(description="The UUID of the approval")
    decision: str = Field(description="approved | rejected | delegated | deferred")
    notes: Optional[str] = Field(None, description="Reason or instructions")
    decided_by: str = Field(description="Name or email of decision maker")

@tool("approval__respond")
async def approval__respond(input_data: ApprovalRespondInput, context: Any = None) -> dict:
    """
    Submit a decision on a pending approval.
    """
    return {
        "approval_id": input_data.approval_id,
        "status": input_data.decision,
        "decided_at": datetime.now().isoformat()
    }

# --- approval__cancel ---
class ApprovalCancelInput(BaseModel):
    approval_id: str = Field(description="The UUID of the approval")
    reason: Optional[str] = Field(None, description="Optional reason for cancellation")

@tool("approval__cancel")
async def approval__cancel(input_data: ApprovalCancelInput, context: Any = None) -> dict:
    """
    Cancel a pending approval request.
    """
    return {
        "approval_id": input_data.approval_id,
        "status": "cancelled"
    }
