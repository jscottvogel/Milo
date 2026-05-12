import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import boto3
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

router = APIRouter(prefix="/v1/slack", tags=["Slack"])

_REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")

def get_slack_token(tenant_id: str) -> Optional[str]:
    secret_name = f"milo/{tenant_id}/slack"
    try:
        client = boto3.client('secretsmanager', region_name=_REGION_NAME)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get('SecretString', '')
        import json
        try:
            secret_dict = json.loads(secret_string)
            return secret_dict.get('slack_bot_token', secret_string)
        except json.JSONDecodeError:
            return secret_string
    except Exception as e:
        # Graceful degradation, let the caller handle missing token
        return None

def get_tenant_id_from_request(request: Request) -> str:
    context = getattr(request.state, "auth_context", None)
    if context:
        return context.tenant_id
    return None

class SendMessageInput(BaseModel):
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None

@router.post("/send_message")
async def send_message(request: Request, input_data: SendMessageInput):
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = get_slack_token(tenant_id)
    if not token:
        # Graceful error format
        return {
            "error": "Slack integration is not configured for this tenant.",
            "success": False
        }
        
    client = AsyncWebClient(token=token)
    
    try:
        kwargs = {
            "channel": input_data.channel,
            "text": input_data.text
        }
        if input_data.blocks:
            kwargs["blocks"] = input_data.blocks
            
        response = await client.chat_postMessage(**kwargs)
        
        return {
            "success": True,
            "result": {
                "message_ts": response.get("ts"),
                "channel": response.get("channel")
            }
        }
    except SlackApiError as e:
        return {
            "success": False,
            "error": f"Slack API Error: {e.response['error']}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
