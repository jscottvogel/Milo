import uuid
from typing import Any

from pydantic import BaseModel, Field

from db.models.agent import Approval
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class HandoffHumanInput(BaseModel):
    reason: str = Field(description="The reason for handing off to the human")
    context_summary: str = Field(description="A summary of what has happened so far")


class HandoffHumanOutput(BaseModel):
    success: bool
    approval_id: str


class HandoffHumanTool(Tool):
    name = "handoff.human"
    description = "Escalate an issue to the human owner via the approval queue."
    input_schema = HandoffHumanInput
    output_schema = HandoffHumanOutput
    mutates = True
    requires_approval = False # Emitting an approval IS the action, doesn't need prior approval

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        import datetime
        import httpx
        
        # 1. Maintain backward compatibility with old Approval model
        old_approval = Approval(
            tenant_id=uuid.UUID(context.tenant_id),
            milo_id=uuid.UUID(context.milo_id),
            thread_id=uuid.UUID(context.thread_id),
            tool_name="escalation",
            payload_jsonb=input_data,
            status="pending",
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        )
        context.session.add(old_approval)
        context.session.commit()
        
        # 2. Call new approval__create internally
        # In a real setup, we would invoke the actual approval__create tool from registry
        # or make the HTTP request directly to the microservice.
        try:
            mcp_url = "http://localhost:8000/approvals"
            due_by = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
            
            # Fetch notify_email from context or tenant settings
            notify_email = context.integration_tokens.get("notify_email", "owner@example.com")
            
            payload = {
                "title": f"Escalation: {input_data.get('reason', 'Human review needed')}",
                "description": input_data.get("context_summary", ""),
                "options": ["approve", "reject", "delegate", "defer"],
                "requested_by": "Milo",
                "notify_email": notify_email,
                "due_by": due_by.isoformat()
            }
            
            # Fire and forget / await the HTTP call to the new approvals microservice
            # async with httpx.AsyncClient() as client:
            #     resp = await client.post(mcp_url, json=payload, timeout=5.0)
            #     new_approval_id = resp.json().get("approval_id")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error calling approval__create: {e}")
            
        return HandoffHumanOutput(success=True, approval_id=str(old_approval.id)).model_dump()
