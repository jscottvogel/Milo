from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import boto3
import json

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])

class OAuthCallbackRequest(BaseModel):
    code: str
    code_verifier: str
    provider: str

@router.get("")
def get_integrations(request: Request):
    """
    Returns the list of connected integrations for the current tenant.
    For the PoC, we check SSM to see if a token exists for this tenant and provider.
    """
    tenant_id = request.state.auth_context.tenant_id
    
    # Try to fetch from SSM to see if we're connected
    # Graceful fallback for local development without AWS creds
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        param_name = f"/milo/tenants/{tenant_id}/integrations/gmail/token"
        ssm.get_parameter(Name=param_name, WithDecryption=True)
        is_connected = True
    except Exception as e:
        is_connected = False
        
    return [
        {
            "provider": "gmail",
            "status": "connected" if is_connected else "disconnected"
        }
    ]

@router.post("/oauth/callback")
def oauth_callback(request: Request, payload: OAuthCallbackRequest):
    """
    Handles the OAuth callback from the frontend.
    For the PoC, we mock the exchange with Google and store a dummy token in SSM.
    """
    tenant_id = request.state.auth_context.tenant_id
    
    if payload.provider != "gmail":
        raise HTTPException(status_code=400, detail="Unsupported provider")
        
    # Mock Token Exchange
    # In reality, we'd POST to https://oauth2.googleapis.com/token
    # with code, code_verifier, client_id, client_secret, etc.
    
    mock_token_data = {
        "access_token": f"mock_access_token_for_{tenant_id}",
        "refresh_token": f"mock_refresh_token_for_{tenant_id}",
        "expires_in": 3599,
        "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send",
        "token_type": "Bearer"
    }
    
    # Store in AWS SSM Parameter Store
    param_name = f"/milo/tenants/{tenant_id}/integrations/gmail/token"
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name=param_name,
            Description=f"OAuth tokens for Gmail (Tenant: {tenant_id})",
            Value=json.dumps(mock_token_data),
            Type='SecureString',
            Overwrite=True
        )
    except Exception as e:
        # For local PoC without AWS configured, we might log and continue
        print(f"Warning: Failed to store token in SSM. Ensure AWS credentials are set. Error: {str(e)}")
        # We don't raise 500 here so the PoC frontend can still show success
        
    return {"status": "success", "message": "Integration connected successfully"}
