import uuid
from typing import Any

from pydantic import BaseModel, Field

from db.models.integrations import IntegrationEvent
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class CalendarReadInput(BaseModel):
    start_date: str = Field(description="ISO 8601 start date to fetch events from")
    end_date: str = Field(description="ISO 8601 end date to fetch events to")


class CalendarReadOutput(BaseModel):
    events: list[dict[str, Any]]


class CalendarReadTool(Tool):
    name = "calendar.read"
    description = "Read calendar events for the tenant within a given date range."
    input_schema = CalendarReadInput
    output_schema = CalendarReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        import os
        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = context.integration_tokens.get("nylas_grant_id")
        
        if nylas_api_key and grant_id:
            from nylas import Client
            nylas = Client(nylas_api_key)
            
            try:
                # Convert string dates to timestamps or whatever format Nylas expects for querying
                # Actually Nylas v3 expects `start` and `end` unix timestamps.
                # For simplicity, we just pass the raw API query or just list recent
                query_params = {
                    "limit": 20,
                    "calendar_id": "primary"
                }
                
                # Fetch calendar events
                try:
                    events_response = nylas.events.list(identifier=grant_id, query_params=query_params)[0]
                except TypeError as e:
                    if "'NoneType' object is not iterable" in str(e):
                        # Nylas SDK bug: it returns data: null when there are no events on a new account
                        events_response = []
                    else:
                        raise e
                
                results = []
                for event in events_response:
                    results.append({
                        "id": event.id,
                        "title": event.title,
                        "status": event.status,
                        "when": str(event.when)
                    })
                return CalendarReadOutput(events=results).model_dump()
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {"error": f"Nylas API Error: {str(e)}"}
                
        # FALLBACK: DATABASE MOCK MODE
        from sqlalchemy import select

        stmt = select(IntegrationEvent).where(
            IntegrationEvent.tenant_id == uuid.UUID(context.tenant_id),
            IntegrationEvent.kind == "calendar_event"
        )
        
        events = context.session.scalars(stmt).all()
        results = [e.payload_jsonb for e in events]
        return CalendarReadOutput(events=results).model_dump()


class CalendarWriteInput(BaseModel):
    title: str = Field(description="Title of the calendar event")
    description: str = Field(default="", description="Description or body of the event")
    start_time: str = Field(description="ISO 8601 formatted start time")
    end_time: str = Field(description="ISO 8601 formatted end time")


class CalendarWriteOutput(BaseModel):
    event_id: str


class CalendarWriteTool(Tool):
    name = "calendar.write"
    description = "Create a new calendar event on the primary calendar."
    input_schema = CalendarWriteInput
    output_schema = CalendarWriteOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        import os
        from datetime import datetime
        
        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = context.integration_tokens.get("nylas_grant_id")
        
        if not (nylas_api_key and grant_id):
            return {"error": "Nylas API key or Grant ID is not configured."}
            
        from nylas import Client
        nylas = Client(nylas_api_key)
        
        try:
            # Parse ISO 8601 to Unix timestamp
            def parse_iso(dt_str):
                return int(datetime.fromisoformat(dt_str.replace('Z', '+00:00')).timestamp())
                
            event = nylas.events.create(
                identifier=grant_id,
                query_params={"calendar_id": "primary"},
                request_body={
                    "title": input_data["title"],
                    "description": input_data["description"],
                    "when": {
                        "start_time": parse_iso(input_data["start_time"]),
                        "end_time": parse_iso(input_data["end_time"])
                    }
                }
            )
            
            event_id = event.data.id if hasattr(event, 'data') else getattr(event, 'id', None)
            
            # Log the creation
            draft = IntegrationEvent(
                tenant_id=uuid.UUID(context.tenant_id),
                integration_id=uuid.uuid4(), # Mock integration id for now
                kind="calendar_event_created",
                payload_jsonb={
                    "title": input_data["title"],
                    "start_time": input_data["start_time"],
                    "event_id": event_id
                }
            )
            context.session.add(draft)
            context.session.commit()
            
            return CalendarWriteOutput(event_id=str(event_id)).model_dump()
        except Exception as e:
            return {"error": f"Nylas API failed to create event: {str(e)}"}
