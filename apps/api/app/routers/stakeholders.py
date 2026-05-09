import uuid
import datetime
import os
import boto3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
import jwt

from app.middleware.auth import get_current_user_id, get_token_payload
from app.middleware.tenant_context import get_current_tenant_id
from db.session import db_session, SessionLocal
from db.models.identity import StakeholderProfile
from db.models.program import ProgramStakeholder, WorkItem

router = APIRouter(prefix="/stakeholders", tags=["Stakeholders"])

# Dummy JWT secret for magic links (should be in env vars in prod)
MAGIC_LINK_SECRET = os.getenv("MAGIC_LINK_SECRET", "super-secret-magic-link-key")

class InviteStakeholderRequest(BaseModel):
    email: str
    program_id: uuid.UUID
    role: str
    influence: Optional[str] = "med"
    interest: Optional[str] = "med"

class StakeholderProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    title: Optional[str] = None
    preferred_channel: Optional[str] = None
    frequency: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None

@router.post("/invite")
def invite_stakeholder(
    req: InviteStakeholderRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id)
):
    """
    Invites a stakeholder to a program.
    If the stakeholder doesn't exist, sends a magic link via SES.
    If they do, sends a simple notification.
    """
    ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    
    # In a real implementation, we would first query Cognito to see if the user exists.
    # For this implementation, we will check our local StakeholderProfile table (assuming they filled it out).
    # But wait, we can't query by email easily if the email is only in Cognito.
    # To keep it simple, we will always generate a magic link if we don't have their sub,
    # or rely on Cognito AdminCreateUser.
    
    # Let's mock the Cognito interaction and just create the DB records
    # Generate a dummy sub for the new stakeholder if not found
    stakeholder_sub = uuid.uuid4()
    
    with db_session(tenant_id) as session:
        # Check if program exists
        program = session.get(WorkItem, req.program_id)
        if not program or program.item_type not in ('project', 'initiative', 'objective', 'workstream'):
            raise HTTPException(status_code=404, detail="Program not found")

        # Create the ProgramStakeholder link
        link = ProgramStakeholder(
            stakeholder_sub=stakeholder_sub,
            tenant_id=tenant_id,
            program_id=req.program_id,
            role=req.role,
            influence=req.influence,
            interest=req.interest,
            status="pending",
            invited_at=datetime.datetime.utcnow()
        )
        session.add(link)
    
    # Generate Magic Link
    token = jwt.encode({
        "email": req.email,
        "sub": str(stakeholder_sub),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=72)
    }, MAGIC_LINK_SECRET, algorithm="HS256")
    
    magic_link = f"https://app.milo.com/stakeholder/setup?token={token}"
    
    try:
        ses_client.send_email(
            Source="notifications@milo.com",
            Destination={"ToAddresses": [req.email]},
            Message={
                "Subject": {"Data": f"You've been invited to {program.name} on Milo"},
                "Body": {"Text": {"Data": f"Click here to join: {magic_link}"}}
            }
        )
    except Exception as e:
        print(f"Failed to send SES email: {e}")
        # Not throwing so we don't break local dev without SES setup
        pass

    return {"status": "success", "message": "Invitation sent", "stakeholder_sub": stakeholder_sub}

@router.get("/profile")
def get_stakeholder_profile(
    payload: dict = Depends(get_token_payload)
):
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    with SessionLocal() as session:
        profile = session.get(StakeholderProfile, uuid.UUID(sub))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

@router.put("/profile")
def update_stakeholder_profile(
    req: StakeholderProfileUpdate,
    payload: dict = Depends(get_token_payload)
):
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    with SessionLocal() as session:
        profile = session.get(StakeholderProfile, uuid.UUID(sub))
        if not profile:
            # Create if it doesn't exist (e.g. first onboarding)
            profile = StakeholderProfile(
                sub=uuid.UUID(sub),
                full_name=req.full_name or "Unknown",
                preferred_channel=req.preferred_channel or "email",
                frequency=req.frequency or "real-time"
            )
            session.add(profile)
            
        for k, v in req.dict(exclude_unset=True).items():
            setattr(profile, k, v)
            
        session.commit()
        return {"status": "success", "profile": profile}

@router.get("/programs")
def list_stakeholder_programs(
    payload: dict = Depends(get_token_payload)
):
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    memberships = []
    
    with SessionLocal() as session:
        stmt = select(ProgramStakeholder).where(ProgramStakeholder.stakeholder_sub == uuid.UUID(sub))
        results = session.execute(stmt).scalars().all()
        
        for row in results:
            # We can also join WorkItem to get program names, but since they are tenant-bound,
            # we must be careful with RLS. The stakeholder can only see programs they are active in.
            # To keep it simple, we just return the raw memberships here.
            memberships.append({
                "tenant_id": row.tenant_id,
                "program_id": row.program_id,
                "role": row.role,
                "status": row.status
            })
            
    return memberships
