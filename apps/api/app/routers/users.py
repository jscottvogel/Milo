from fastapi import APIRouter, Request, HTTPException
import uuid

from db.models import User, Membership
from app.middleware.auth import RequestContext

router = APIRouter(prefix="/v1", tags=["users"])

@router.get("/me")
def get_me(request: Request):
    context: RequestContext = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    user_id = uuid.UUID(context.sub) if context.sub != "dev-user" else uuid.uuid4()
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    
    # For PoC if user doesn't exist but has a token, we could auto-create or just return 404
    if not user:
        if context.sub == "dev-user":
            # Just return a mock response for dev
            return {
                "id": str(user_id),
                "email": context.email,
                "name": "Dev User",
                "memberships": [{"tenant_id": context.tenant_id, "role": "admin"}]
            }
        raise HTTPException(status_code=404, detail="User not found")
        
    memberships = db.query(Membership).filter(Membership.user_id == user_id).all()
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "memberships": [
            {
                "tenant_id": str(m.tenant_id),
                "role": m.role
            } for m in memberships
        ]
    }
