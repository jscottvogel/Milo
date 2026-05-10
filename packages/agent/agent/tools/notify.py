from typing import Any, Literal
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool
from agent.push import manager

class PushNotifyInput(BaseModel):
    recipient: str = Field(description="The recipient identifier, e.g., an email address like j_scott_vogel@yahoo.com")
    message: str = Field(description="The body of the notification. The first line will be used as the subject if sent via email.")
    channel: Literal["email"] = Field(default="email", description="The channel to send the notification over. Currently only 'email' is supported.")

class PushNotifyOutput(BaseModel):
    status: str = Field(description="Delivery status")
    message_id: str | None = Field(default=None, description="The internal ID or external ID of the notification sent")
    error: str | None = Field(default=None, description="Error message if delivery failed")

class PushNotifyTool(Tool):
    name = "push.notify"
    description = "Send a proactive push notification or alert to the user. Use this to notify the user of triggers or daily briefings without human prompt."
    input_schema = PushNotifyInput
    output_schema = PushNotifyOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        recipient = input_data["recipient"]
        message = input_data["message"]
        channel = input_data.get("channel", "email")
        
        result = await manager.notify(recipient, message, context, channel_name=channel)
        
        return PushNotifyOutput(
            status=result.get("status", "error"),
            message_id=result.get("message_id"),
            error=result.get("error")
        ).model_dump()
