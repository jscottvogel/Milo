import uuid
from typing import Any

from pydantic import BaseModel, Field

from db.models.integrations import IntegrationEvent
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class EmailDraftInput(BaseModel):
    to: str = Field(description="The email address to send the draft to")
    subject: str = Field(description="The subject line of the email")
    body: str = Field(description="The body of the email")


class EmailDraftOutput(BaseModel):
    draft_id: str = Field(description="The ID of the persisted draft row")


class EmailDraftTool(Tool):
    name = "email.draft"
    description = "Produce an email body and subject, persist it as a draft, and return the draft ID. This does NOT send the email."
    input_schema = EmailDraftInput
    output_schema = EmailDraftOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        # We store the draft as an IntegrationEvent with kind='email_draft'
        # In a real system, integration_id would be looked up based on active email integrations.
        # For the PoC draft tool, we can use a placeholder integration_id or allow it to be null
        # Wait, integration_id is not nullable in IntegrationEvent.
        # We need an active integration. For now, we will look up any active email integration,
        # or we create a dummy one if none exists (for testing purposes).
        from db.models.integrations import Integration
        from sqlalchemy import select

        stmt = select(Integration).where(
            Integration.tenant_id == uuid.UUID(context.tenant_id),
            Integration.kind.in_(["gmail", "outlook"])
        ).limit(1)
        
        integration = context.session.scalar(stmt)
        if not integration:
            # For the PoC, we will auto-create a dummy gmail integration if none exists
            integration = Integration(
                tenant_id=uuid.UUID(context.tenant_id),
                kind="gmail",
                credentials_jsonb={},
                status="active"
            )
            context.session.add(integration)
            context.session.flush()

        draft = IntegrationEvent(
            tenant_id=uuid.UUID(context.tenant_id),
            integration_id=integration.id,
            kind="email_draft",
            payload_jsonb={
                "to": input_data["to"],
                "subject": input_data["subject"],
                "body": input_data["body"]
            }
        )
        context.session.add(draft)
        context.session.commit()

        return EmailDraftOutput(draft_id=str(draft.id)).model_dump()
