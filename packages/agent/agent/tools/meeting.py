import uuid
from typing import Any

from pydantic import BaseModel, Field

from db.models.integrations import IntegrationEvent
from agent.tools.context import AgentContext
from agent.tools.registry import Tool

class MeetingAttendInput(BaseModel):
    meeting_link: str = Field(description="The full URL to the Zoom, Microsoft Teams, or Google Meet meeting.")
    name: str = Field(default="Milo AI", description="The name the bot should display when joining the meeting.")

class MeetingAttendOutput(BaseModel):
    notetaker_id: str
    status: str

class MeetingAttendTool(Tool):
    name = "meeting__attend"
    description = "Deploy the Nylas Notetaker bot to attend, record, and transcribe a Zoom, Teams, or Google Meet session."
    input_schema = MeetingAttendInput
    output_schema = MeetingAttendOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        import os
        
        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = context.integration_tokens.get("nylas_grant_id")
        
        if not (nylas_api_key and grant_id):
            return {"error": "Nylas API key or Grant ID is not configured."}
            
        from nylas import Client
        nylas = Client(nylas_api_key)
        
        try:
            # Deploy the Notetaker bot
            response = nylas.notetakers.invite(
                identifier=grant_id,
                request_body={
                    "meeting_link": input_data["meeting_link"],
                    "name": input_data.get("name", "Milo AI")
                }
            )
            
            notetaker_id = response.data.id if hasattr(response, 'data') else getattr(response, 'id', 'unknown')
            
            # Log the deployment
            draft = IntegrationEvent(
                tenant_id=uuid.UUID(context.tenant_id),
                integration_id=uuid.uuid4(), # Mock integration id for now
                kind="meeting_bot_deployed",
                payload_jsonb={
                    "meeting_link": input_data["meeting_link"],
                    "notetaker_id": notetaker_id
                }
            )
            context.session.add(draft)
            context.session.commit()
            
            return MeetingAttendOutput(
                notetaker_id=str(notetaker_id),
                status="deployed"
            ).model_dump()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Nylas Notetaker Failed: {str(e)}")
            return {"error": f"Nylas API failed to deploy Notetaker bot: {str(e)}"}
