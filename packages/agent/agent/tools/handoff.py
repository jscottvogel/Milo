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
    name = "handoff__human"
    description = "Escalate an issue to the human owner via the approval queue."
    input_schema = HandoffHumanInput
    output_schema = HandoffHumanOutput
    mutates = True
    requires_approval = False # Emitting an approval IS the action, doesn't need prior approval

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        import datetime
        from agent.tools.approval_tools import ApprovalCreateTool
        
        # We invoke the ApprovalCreateTool natively
        approval_tool = ApprovalCreateTool()
        
        # Fetch notify_email from context or tenant settings
        notify_email = context.integration_tokens.get("notify_email", "owner@example.com")
        due_by = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        
        payload = {
            "title": f"Escalation: {input_data.get('reason', 'Human review needed')}",
            "description": input_data.get("context_summary", ""),
            "options": ["approve", "reject", "delegate", "defer"],
            "requested_by": "Milo Agent (Handoff)",
            "notify_email": notify_email,
            "due_by": due_by.isoformat()
        }
        
        try:
            result = await approval_tool.invoke(payload, context)
            new_approval_id = result.get("approval_id", "unknown")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error calling approval__create: {e}")
            new_approval_id = "error"
            
        return HandoffHumanOutput(success=True, approval_id=new_approval_id).model_dump()
