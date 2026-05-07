from fastapi import APIRouter, Request, HTTPException
import uuid
import boto3
from pydantic import BaseModel

from db.models import Tenant, User, Membership
from app.middleware.auth import RequestContext
from app.config import settings

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])

class CreateTenantRequest(BaseModel):
    name: str
    slug: str

@router.post("")
def create_tenant(request: Request, payload: CreateTenantRequest):
    context: RequestContext = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = uuid.uuid4()
    
    # In a real app, you'd check if slug is unique, etc.
    tenant = Tenant(id=tenant_id, name=payload.name, slug=payload.slug)
    db.add(tenant)
    db.commit()
    
    # Update Cognito user with custom:tenant_id
    if settings.COGNITO_USER_POOL_ID and context.sub != "dev-user":
        client = boto3.client('cognito-idp', region_name=settings.AWS_REGION)
        try:
            client.admin_update_user_attributes(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=context.sub,
                UserAttributes=[
                    {
                        'Name': 'custom:tenant_id',
                        'Value': str(tenant_id)
                    },
                    {
                        'Name': 'custom:role',
                        'Value': 'owner'
                    }
                ]
            )
        except Exception as e:
            # Rollback if cognito fails
            db.delete(tenant)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to update Cognito: {str(e)}")
            
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug
    }

@router.get("/{id}")
def get_tenant(request: Request, id: uuid.UUID):
    context: RequestContext = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    if str(id) != context.tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only access your own tenant")
        
    db = getattr(request.state, "db", None)
    
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "plan": tenant.plan
    }
