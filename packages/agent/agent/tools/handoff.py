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
        
        approval = Approval(
            tenant_id=uuid.UUID(context.tenant_id),
            milo_id=uuid.UUID(context.milo_id),
            thread_id=uuid.UUID(context.thread_id),
            tool_name="escalation",
            payload_jsonb=input_data,
            status="pending",
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        )
        context.session.add(approval)
        context.session.commit()
        
        return HandoffHumanOutput(success=True, approval_id=str(approval.id)).model_dump()
