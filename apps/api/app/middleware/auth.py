import json
from collections.abc import Callable

import httpx
from app.config import settings
from fastapi import Request, Response
from jose import jwk, jwt
from jose.utils import base64url_decode
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# JWKS Cache
_jwks = {}

def get_jwks(pool_id: str):
    global _jwks
    if pool_id not in _jwks:
        if not pool_id:
            return {}

        jwks_url = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{pool_id}/.well-known/jwks.json"
        try:
            response = httpx.get(jwks_url)
            response.raise_for_status()
            _jwks[pool_id] = response.json()
        except Exception:
            _jwks[pool_id] = {}
    return _jwks[pool_id]

class RequestContext(BaseModel):
    sub: str
    email: str
    tenant_id: str
    role: str

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Public endpoints that bypass auth
        if request.url.path in ["/v1/health", "/docs", "/openapi.json"] or request.url.path.startswith("/v1/webhooks"):
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
            # For local dev/testing without Cognito or when simulating local requests
            if token.startswith("dev_"):
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
                # We need to figure out which pool this token is from.
                # Let's decode the unverified claims to get the issuer.
                claims = jwt.get_unverified_claims(token)
                issuer = claims.get("iss")
                
                tenant_issuer = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
                stakeholder_issuer = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.STAKEHOLDER_USER_POOL_ID}"
                
                if issuer == tenant_issuer:
                    pool_id = settings.COGNITO_USER_POOL_ID
                    is_stakeholder = False
                elif issuer == stakeholder_issuer:
                    pool_id = settings.STAKEHOLDER_USER_POOL_ID
                    is_stakeholder = True
                else:
                    raise ValueError("Invalid issuer")

                # Retrieve JWKS
                keys = get_jwks(pool_id).get("keys", [])
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

                if claims.get("token_use") != "id":
                    raise ValueError("Expected an ID token")

                if is_stakeholder:
                    memberships_str = claims.get("custom:tenant_memberships", "[]")
                    memberships = json.loads(memberships_str)
                    
                    # For a stakeholder, the request path usually indicates the tenant, 
                    # or they might be accessing their global profile.
                    # We will store the memberships in the auth context.
                    # If the request requires a specific tenant, TenantContextMiddleware will validate it against memberships.
                    
                    # To fulfill RequestContext, we set tenant_id to the first active one or empty if none.
                    # We'll also store the memberships in request.state for downstream checks.
                    active_tenant = memberships[0]["tenant_id"] if memberships else ""
                    
                    context = RequestContext(
                        sub=claims["sub"],
                        email=claims.get("email", ""),
                        tenant_id=active_tenant,
                        role="stakeholder"
                    )
                    request.state.tenant_memberships = memberships
                else:
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

def get_current_user_id(request: Request) -> str:
    return getattr(request.state, "user_id", None)

def get_token_payload(request: Request) -> dict:
    context = getattr(request.state, "auth_context", None)
    if context:
        return {"sub": context.sub, "email": context.email}
    return {}
