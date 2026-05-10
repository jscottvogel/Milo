import logging
import httpx
from typing import Any, Optional
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

logger = logging.getLogger(__name__)

class PortfolioReadInput(BaseModel):
    status: Optional[str] = Field(default=None, description="Filter portfolio programs by status (e.g. 'active', 'planned', 'complete')")
    owner_name: Optional[str] = Field(default=None, description="Filter portfolio programs by owner name")

class PortfolioReadOutput(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

class PortfolioReadTool(Tool):
    name = "portfolio__read"
    description = "Read the overall portfolio view across all active programs for the tenant, returning aggregated health (RAG), milestone count, overdue tasks, and budget variance."
    input_schema = PortfolioReadInput
    output_schema = PortfolioReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        try:
            # We call the local FastAPI endpoint
            # Since the agent runs locally with the API, we can hit localhost:8000
            # Alternatively, we could construct the DB query here, but reusing the endpoint ensures consistency.
            api_url = "http://127.0.0.1:8000/v1/portfolio"
            
            params = {}
            if input_data.get("status"):
                params["status"] = input_data["status"]
            if input_data.get("owner_name"):
                params["owner_name"] = input_data["owner_name"]
                
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer dev_{context.tenant_id}"}
                resp = await client.get(api_url, params=params, headers=headers, timeout=10.0)
                
                if resp.status_code == 200:
                    return PortfolioReadOutput(success=True, data=resp.json()).model_dump()
                else:
                    return PortfolioReadOutput(success=False, data=None, error=resp.text).model_dump()
                    
        except Exception as e:
            logger.error(f"Error calling portfolio endpoint: {e}")
            return PortfolioReadOutput(success=False, data=None, error=str(e)).model_dump()
