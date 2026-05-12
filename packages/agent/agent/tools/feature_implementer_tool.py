import os
import json
import logging
from typing import Any, Optional, List

from pydantic import BaseModel, Field
import mcp.client.stdio
from mcp.client.session import ClientSession

from .context import AgentContext
from .registry import Tool

logger = logging.getLogger(__name__)

class FeatureImplementerInput(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the local GitHub repo directory")
    feature_prompt: str = Field(..., description="Natural language description of the feature to implement")
    target_files: Optional[List[str]] = Field(None, description="Specific files/dirs to scope the changes to")
    review_mode: bool = Field(False, description="If true, show diffs and wait for explicit 'approve' or 'reject' before writing any files")
    dry_run: bool = Field(False, description="If true, return the plan and diffs without writing files")
    session_id: Optional[str] = Field(None, description="If continuing a review session, provide the session ID")
    approved: Optional[bool] = Field(None, description="If continuing a review session, whether the changes are approved")

class FeatureImplementerOutput(BaseModel):
    plan: Optional[List[str]] = None
    changes: Optional[List[dict]] = None
    status: Optional[str] = None
    summary: str
    warnings: Optional[List[str]] = None
    session_id: Optional[str] = None

class FeatureImplementerTool(Tool):
    name = "implement_feature"
    description = "Uses an LLM via an MCP server to automatically plan and implement a feature by creating or modifying files in a local repository."
    input_schema = FeatureImplementerInput
    output_schema = FeatureImplementerOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        # Standard path for the Node MCP server built previously
        server_path = "c:/Users/j_sco/projects/Milo/Milo/tools/mcp-feature-implementer/dist/index.js"
        
        env = os.environ.copy()
        if "ANTHROPIC_API_KEY" not in env:
            logger.warning("ANTHROPIC_API_KEY is not set in the environment. MCP feature implementer may fail.")

        server_params = mcp.client.stdio.StdioServerParameters(
            command="node",
            args=[server_path],
            env=env
        )

        try:
            async with mcp.client.stdio.stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        "implement_feature",
                        arguments=input_data
                    )
                    
                    if result.isError:
                        return {"summary": f"MCP tool returned an error: {result.content}"}
                        
                    if result.content and len(result.content) > 0 and getattr(result.content[0], "type", "") == "text":
                        try:
                            parsed = json.loads(result.content[0].text)
                            return parsed
                        except Exception as e:
                            return {"summary": f"Failed to parse JSON response from MCP. Error: {e}"}
                    elif isinstance(result.content, list) and len(result.content) > 0 and isinstance(result.content[0], dict):
                        # Some versions of the SDK might return raw dicts instead of TextContent objects
                        if result.content[0].get("type") == "text":
                            try:
                                parsed = json.loads(result.content[0].get("text", ""))
                                return parsed
                            except Exception as e:
                                return {"summary": f"Failed to parse JSON response from MCP dictionary. Error: {e}"}
                    
                    return {"summary": "Successfully executed, but response format was not recognized."}
        except Exception as e:
            logger.error(f"Error calling MCP feature implementer: {e}")
            return {"summary": f"Error calling MCP feature implementer: {str(e)}"}
