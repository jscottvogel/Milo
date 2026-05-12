import uuid
from typing import Any
from pydantic import BaseModel, Field
import httpx

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

class StakeholderInviteInput(BaseModel):
    email: str = Field(description="The email address of the stakeholder to invite.")
    program_id: str = Field(description="The UUID of the program the stakeholder is being invited to.")
    role: str = Field(description="The role of the stakeholder in the program (e.g., 'sponsor', 'reviewer', 'observer').")
    influence: str = Field(default="med", description="Influence level: 'low', 'med', 'high'.")
    interest: str = Field(default="med", description="Interest level: 'low', 'med', 'high'.")

class StakeholderInviteOutput(BaseModel):
    status: str
    message: str
    stakeholder_sub: str

class StakeholderInviteTool(Tool):
    name = "stakeholder__invite"
    description = "Invite a new or existing stakeholder to a program. This will trigger an email invitation with a magic link."
    input_schema = StakeholderInviteInput
    output_schema = StakeholderInviteOutput
    mutates = True
    requires_approval = True

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        # In a real agent environment, this tool would hit the FastAPI endpoint directly or use the same local DB logic.
        # Let's hit the local FastAPI endpoint.
        
        # We need the tenant_id in the auth headers or context. 
        # Since the agent runs locally with the DB, we can just instantiate the DB models directly, 
        # OR we can hit the API if we have an internal base URL.
        # It's safer to use the DB directly to avoid auth loops.
        
        from db.session import SessionLocal
        from db.models.program import ProgramStakeholder, WorkItem
        import datetime
        
        stakeholder_sub = uuid.uuid4()
        
        with SessionLocal() as session:
            # Note: We aren't doing the SES email here because the API is responsible for that.
            # Ideally the tool just calls the API. But let's assume the tool implements the DB insert.
            # Actually, calling the local API is better if we want SES to fire.
            
            # Since the API is at localhost:8000
            headers = {
                "Authorization": f"Bearer dev_{context.tenant_id}"
            }
            
            payload = {
                "email": input_data["email"],
                "program_id": input_data["program_id"],
                "role": input_data["role"],
                "influence": input_data["influence"],
                "interest": input_data["interest"]
            }
            
            try:
                # Assuming the API is running locally
                # If we are in the lambda, we might need a different URL, but for the agent we assume it can hit the API.
                # Actually, the agent is part of the API process! It runs inside the FastAPI worker.
                # So we can just import the router function directly.
                from app.routers.stakeholders import invite_stakeholder, InviteStakeholderRequest
                
                req = InviteStakeholderRequest(**payload)
                res = invite_stakeholder(req=req, current_user_id=uuid.UUID(int=0), tenant_id=uuid.UUID(context.tenant_id))
                return StakeholderInviteOutput(
                    status=res["status"],
                    message=res["message"],
                    stakeholder_sub=str(res["stakeholder_sub"])
                ).model_dump()
            except Exception as e:
                raise ValueError(f"Failed to invite stakeholder: {e}")

class StakeholderReadInput(BaseModel):
    program_id: str | None = Field(None, description="The UUID of the program to fetch stakeholders for.")
    stakeholder_id: str | None = Field(None, description="The UUID of a specific stakeholder to read.")
    status: str | None = Field(None, description="Filter by status: 'pending', 'active', 'revoked'.")

class StakeholderSearchInput(BaseModel):
    query: str | None = Field(None, description="Free-text search against email and role.")
    role: str | None = Field(None, description="Filter by role (e.g. sponsor, reviewer).")
    influence: str | None = Field(None, description="Filter by influence: 'low', 'med', 'high'.")
    interest: str | None = Field(None, description="Filter by interest: 'low', 'med', 'high'.")
    status: str | None = Field(None, description="Filter by status.")
    limit: int = Field(20, description="Maximum number of stakeholders to return.")

class StakeholderReadTool(Tool):
    name = "stakeholder__read"
    description = "Read stakeholders for a program or fetch a specific stakeholder by ID."
    input_schema = StakeholderReadInput
    output_schema = None # Returns a list of stakeholders
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        params = {}
        if input_data.get("program_id"):
            params["program_id"] = input_data["program_id"]
        if input_data.get("stakeholder_id"):
            params["stakeholder_id"] = input_data["stakeholder_id"]
        if input_data.get("status"):
            params["status"] = input_data["status"]
            
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer dev_{context.tenant_id}"}
            try:
                res = await client.get("http://127.0.0.1:8000/v1/stakeholders", params=params, headers=headers)
                res.raise_for_status()
                return res.json()
            except Exception as e:
                raise ValueError(f"Failed to read stakeholders: {e}")

class StakeholderSearchTool(Tool):
    name = "stakeholder__search"
    description = "Search all stakeholders across all programs for the tenant by query, role, influence, interest, or status."
    input_schema = StakeholderSearchInput
    output_schema = None # Returns a list of stakeholders
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        params = {"limit": input_data.get("limit", 20)}
        if input_data.get("query"): params["query"] = input_data["query"]
        if input_data.get("role"): params["role"] = input_data["role"]
        if input_data.get("influence"): params["influence"] = input_data["influence"]
        if input_data.get("interest"): params["interest"] = input_data["interest"]
        if input_data.get("status"): params["status"] = input_data["status"]
            
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer dev_{context.tenant_id}"}
            try:
                res = await client.get("http://127.0.0.1:8000/v1/stakeholders/search", params=params, headers=headers)
                res.raise_for_status()
                return res.json()
            except Exception as e:
                raise ValueError(f"Failed to search stakeholders: {e}")
