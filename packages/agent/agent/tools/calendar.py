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
        from sqlalchemy import select

        # In Phase 8, this will read from a proper synced table. 
        # For Phase 4, we read from integration_events cache.
        stmt = select(IntegrationEvent).where(
            IntegrationEvent.tenant_id == uuid.UUID(context.tenant_id),
            IntegrationEvent.kind == "calendar_event"
        )
        
        events = context.session.scalars(stmt).all()
        
        # Filtering by date can be done in python for the PoC
        results = [e.payload_jsonb for e in events]
        return CalendarReadOutput(events=results).model_dump()
