import uuid
import os
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import boto3

router = APIRouter(prefix="/v1/inbox", tags=["inbox"])

class EmailResponse(BaseModel):
    id: str
    subject: str
    sender: str
    preview: str
    time: str
    unread: bool

class MeetingResponse(BaseModel):
    id: str
    title: str
    time: str
    attendees: int

def get_nylas_grant(tenant_id: str) -> str | None:
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        param_name = f"/milo/tenants/{tenant_id}/integrations/gmail/token"
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception:
        return None

@router.get("/emails", response_model=list[EmailResponse])
def get_emails(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    grant_id = get_nylas_grant(context.tenant_id)
    nylas_api_key = os.environ.get("NYLAS_API_KEY")
    
    if not grant_id or not nylas_api_key:
        return []
        
    try:
        from nylas import Client
        nylas = Client(nylas_api_key)
        
        # Get 5 most recent emails
        response = nylas.messages.list(
            identifier=grant_id,
            query_params={"limit": 5, "in": "INBOX"}
        )
        
        messages = response[0]
        results = []
        for msg in messages:
            sender = msg.from_[0].get("email", "unknown") if msg.from_ and isinstance(msg.from_[0], dict) else getattr(msg.from_[0], "email", "unknown") if msg.from_ else "unknown"
            
            import datetime
            time_val = "Unknown"
            if msg.date:
                dt = datetime.datetime.fromtimestamp(msg.date, tz=datetime.UTC)
                time_val = dt.strftime("%I:%M %p")
                
            results.append(EmailResponse(
                id=str(msg.id),
                subject=msg.subject or "No Subject",
                sender=sender,
                preview=(msg.snippet or "")[:100],
                time=time_val,
                unread=msg.unread
            ))
            
        return results
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to fetch Nylas emails: {e}")
        return []

@router.get("/meetings", response_model=list[MeetingResponse])
def get_meetings(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    grant_id = get_nylas_grant(context.tenant_id)
    nylas_api_key = os.environ.get("NYLAS_API_KEY")
    
    if not grant_id or not nylas_api_key:
        return []
        
    try:
        from nylas import Client
        nylas = Client(nylas_api_key)
        
        # We need calendar_id. For PoC, just fetch first primary calendar
        cals_response = nylas.calendars.list(identifier=grant_id)
        if not cals_response[0]:
            return []
            
        primary_cal_id = cals_response[0][0].id
        
        import datetime
        now = int(datetime.datetime.now().timestamp())
        end = now + (7 * 24 * 3600)
        
        events_response = nylas.events.list(
            identifier=grant_id,
            query_params={
                "calendar_id": primary_cal_id,
                "start": now,
                "end": end,
                "limit": 5
            }
        )
        
        results = []
        for ev in events_response[0]:
            time_val = "TBD"
            if ev.when and getattr(ev.when, "start_time", None):
                dt = datetime.datetime.fromtimestamp(ev.when.start_time, tz=datetime.UTC)
                time_val = dt.strftime("%a %I:%M %p")
                
            results.append(MeetingResponse(
                id=str(ev.id),
                title=ev.title or "Untitled Event",
                time=time_val,
                attendees=len(ev.participants) if ev.participants else 0
            ))
            
        return results
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to fetch Nylas events: {e}")
        return []
