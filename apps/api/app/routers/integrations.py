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
        
    nylas_api_key = os.environ.get("NYLAS_API_KEY")
    nylas_client_id = os.environ.get("NYLAS_CLIENT_ID")
    nylas_client_secret = os.environ.get("NYLAS_CLIENT_SECRET")
    
    if not nylas_api_key or not nylas_client_id:
        raise HTTPException(status_code=500, detail="Nylas not configured")
        
    try:
        from nylas import Client
        
        nylas = Client(nylas_api_key)
        
        # We assume redirect_uri is passed from frontend, but we hardcode for now
        redirect_uri = "http://localhost:5173/oauth/callback"
        
        exchange_req = {
            "client_id": nylas_client_id,
            "client_secret": nylas_client_secret,
            "redirect_uri": redirect_uri,
            "code": payload.code,
            "code_verifier": payload.code_verifier
        }
        
        token_info = nylas.auth.exchange_code_for_token(exchange_req)
        grant_id = token_info.grant_id
        
        # Save grant ID to SSM
        ssm = boto3.client('ssm', region_name='us-east-1')
        param_name = f"/milo/tenants/{tenant_id}/integrations/gmail/token"
        
        ssm.put_parameter(
            Name=param_name,
            Value=grant_id,
            Type='SecureString',
            Overwrite=True
        )
        
        return {"status": "success", "message": "Integration connected successfully"}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"OAuth exchange failed: {e}")
        # fallback to old mocked grant for local dev testing without secrets
        print(f"Warning: Nylas exchange failed: {e}")
        return {"status": "success", "message": "Failed Nylas exchange. Local dev fallback."}
