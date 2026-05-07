import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import httpx
from jose import jwt, jwk
from jose.utils import base64url_decode
from pydantic import BaseModel

from app.config import settings

# JWKS Cache
_jwks = None

def get_jwks():
    global _jwks
    if _jwks is None:
        if not settings.COGNITO_USER_POOL_ID:
            return {}
            
        jwks_url = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        try:
            response = httpx.get(jwks_url)
            response.raise_for_status()
            _jwks = response.json()
        except Exception:
            _jwks = {}
    return _jwks

class RequestContext(BaseModel):
    sub: str
    email: str
    tenant_id: str
    role: str

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Public endpoints that bypass auth
        if request.url.path in ["/v1/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content=json.dumps({"error": {"code": "UNAUTHORIZED", "message": "Missing token"}}),
                status_code=401,
                media_type="application/json"
            )

        token = auth_header.split(" ")[1]
        
        try:
            # For local dev/testing without Cognito
            if not settings.COGNITO_USER_POOL_ID and token.startswith("dev_"):
                # Expect token like "dev_<tenant_id>"
                parts = token.split("_", 1)
                tenant_id = parts[1] if len(parts) > 1 else ""
                if not tenant_id:
                    raise ValueError("Missing tenant_id in dev token")
                
                context = RequestContext(
                    sub="dev-user",
                    email="dev@example.com",
                    tenant_id=tenant_id,
                    role="admin"
                )
                request.state.tenant_id = context.tenant_id
                request.state.user_id = context.sub
                request.state.auth_context = context
            else:
                # Retrieve JWKS
                keys = get_jwks().get("keys", [])
                if not keys:
                    raise ValueError("No JWKS available")

                # Extract unverified header to find kid
                header = jwt.get_unverified_header(token)
                kid = header.get("kid")
                key = next((k for k in keys if k["kid"] == kid), None)
                
                if not key:
                    raise ValueError("Public key not found")

                # Construct public key
                public_key = jwk.construct(key)
                message, encoded_sig = token.rsplit(".", 1)
                decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
                
                if not public_key.verify(message.encode("utf-8"), decoded_sig):
                    raise ValueError("Signature verification failed")

                # Decode payload
                claims = jwt.get_unverified_claims(token)
                
                # Verify claims (Cognito specifics)
                issuer = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
                if claims.get("iss") != issuer:
                    raise ValueError("Invalid issuer")
                    
                if claims.get("token_use") != "id":
                    raise ValueError("Expected an ID token")

                tenant_id = claims.get("custom:tenant_id")
                if not tenant_id:
                    raise ValueError("Token missing tenant_id claim")

                context = RequestContext(
                    sub=claims["sub"],
                    email=claims.get("email", ""),
                    tenant_id=tenant_id,
                    role=claims.get("custom:role", "user")
                )
                
                request.state.tenant_id = context.tenant_id
                request.state.user_id = context.sub
                request.state.auth_context = context
                
        except Exception as e:
            return Response(
                content=json.dumps({"error": {"code": "UNAUTHORIZED", "message": f"Invalid token: {str(e)}" }}),
                status_code=401,
                media_type="application/json"
            )

        return await call_next(request)
