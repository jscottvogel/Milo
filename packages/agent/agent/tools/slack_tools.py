import logging
import httpx
from typing import Any, Optional
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

logger = logging.getLogger(__name__)

class SlackSendInput(BaseModel):
    channel: str = Field(description="The Slack channel ID or name (e.g., '#general' or 'C12345678')")
    text: str = Field(description="The markdown message text to send to Slack")
    blocks: Optional[list] = Field(default=None, description="Optional Slack Block Kit blocks for rich messaging")

class SlackSendOutput(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

class SlackSendTool(Tool):
    name = "slack__send"
    description = "Send a message or alert to a Slack channel."
    input_schema = SlackSendInput
    output_schema = SlackSendOutput
    mutates = True
    requires_approval = True  # Approval before pinging Slack channels is usually desired

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        token = context.integration_tokens.get("slack_bot_token")
        if not token:
            return SlackSendOutput(
                success=False, 
                data=None, 
                error="Slack integration is not configured or bot token is missing."
            ).model_dump()
            
        payload = {
            "channel": input_data["channel"],
            "text": input_data["text"]
        }
        if input_data.get("blocks"):
            payload["blocks"] = input_data["blocks"]
            
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                resp = await client.post("https://slack.com/api/chat.postMessage", json=payload, headers=headers, timeout=10.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        return SlackSendOutput(success=True, data=data).model_dump()
                    else:
                        return SlackSendOutput(success=False, data=None, error=data.get("error", "Slack API returned an error")).model_dump()
                else:
                    return SlackSendOutput(success=False, data=None, error=resp.text).model_dump()
        except Exception as e:
            logger.error(f"Error calling Slack chat.postMessage: {e}")
            return SlackSendOutput(success=False, data=None, error=str(e)).model_dump()
