import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models.agent import Message, ToolCall, Approval
from db.models.integrations import IntegrationEvent
from db.models.program import WorkItem

router = APIRouter(prefix="/v1/activities", tags=["activities"])

class ActivityResponse(BaseModel):
    id: str
    action: str
    time: str
    type: str

import time

@router.get("", response_model=list[ActivityResponse])
def get_recent_activities(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = uuid.UUID(context.tenant_id)
    
    # We will fetch a mix of activities: approvals, tool calls, integration events
    # For PoC, we just fetch IntegrationEvents and map them to activity format
    stmt = select(IntegrationEvent).where(IntegrationEvent.tenant_id == tenant_id).order_by(IntegrationEvent.created_at.desc()).limit(10)
    events = db.scalars(stmt).all()
    
    activities = []
    for event in events:
        action_text = f"Processed {event.kind}"
        
        if event.kind == "email_sent":
            payload = event.payload_jsonb or {}
            to_addr = payload.get("to", "unknown")
            action_text = f"Emailed {to_addr} regarding {payload.get('subject', 'update')}"
            type_val = "email"
        elif event.kind == "email_draft":
            action_text = "Drafted email (held back due to missing credentials)"
            type_val = "draft"
        else:
            type_val = "system"
            
        # Basic human readable time format mock
        import datetime
        now = datetime.datetime.now(datetime.UTC)
        diff = now - event.created_at.replace(tzinfo=datetime.UTC)
        minutes = int(diff.total_seconds() / 60)
        
        if minutes < 60:
            time_str = f"{minutes} mins ago"
        elif minutes < 1440:
            time_str = f"{int(minutes/60)} hours ago"
        else:
            time_str = f"{int(minutes/1440)} days ago"
            
        activities.append({
            "id": str(event.id),
            "action": action_text,
            "time_str": time_str,
            "type": type_val,
            "ts": event.created_at
        })
        
    # Also fetch recent approvals
    stmt_app = select(Approval).where(Approval.tenant_id == tenant_id).order_by(Approval.created_at.desc()).limit(5)
    approvals = db.scalars(stmt_app).all()
    for app in approvals:
        if app.status == "pending":
            action = f"Requested approval for {app.tool_name}"
        else:
            action = f"Action {app.tool_name} was {app.status}"
            
        now = datetime.datetime.now(datetime.UTC)
        diff = now - app.created_at.replace(tzinfo=datetime.UTC)
        minutes = int(diff.total_seconds() / 60)
        time_str = f"{minutes} mins ago" if minutes < 60 else f"{int(minutes/60)} hours ago" if minutes < 1440 else f"{int(minutes/1440)} days ago"
            
        activities.append({
            "id": str(app.id), "action": action, "time_str": time_str, "type": "approval", "ts": app.created_at
        })
        
    # Also fetch recent work items
    stmt_wi = select(WorkItem).where(WorkItem.tenant_id == tenant_id).order_by(WorkItem.created_at.desc()).limit(5)
    work_items = db.scalars(stmt_wi).all()
    for wi in work_items:
        action = f"Added {wi.item_type} '{wi.name}'"
        if wi.status == 'completed': action = f"Completed {wi.item_type} '{wi.name}'"
        
        now = datetime.datetime.now(datetime.UTC)
        diff = now - wi.created_at.replace(tzinfo=datetime.UTC)
        minutes = int(diff.total_seconds() / 60)
        time_str = f"{minutes} mins ago" if minutes < 60 else f"{int(minutes/60)} hours ago" if minutes < 1440 else f"{int(minutes/1440)} days ago"
        
        activities.append({
            "id": str(wi.id), "action": action, "time_str": time_str, "type": "system", "ts": wi.created_at
        })
        
    # Sort them by timestamp descending
    activities.sort(key=lambda x: x["ts"].timestamp(), reverse=True)
    
    return [ActivityResponse(id=a["id"], action=a["action"], time=a["time_str"], type=a["type"]) for a in activities[:10]]
