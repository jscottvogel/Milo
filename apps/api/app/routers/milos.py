import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.identity import Milo, User, Membership
import boto3
import os
import json
router = APIRouter(prefix="/v1/milos", tags=["milos"])


class AutonomyUpdateRequest(BaseModel):
    autonomy_levels: dict[str, str] = Field(..., description="Map of tool class to autonomy level (draft, copilot, auto)")


class MiloResponse(BaseModel):
    id: str
    name: str
    persona_pack: str
    autonomy_levels: dict[str, str]
    briefing_send_time: str
    briefing_enabled: bool

class UpdateBriefingRequest(BaseModel):
    briefing_send_time: str = Field(..., description="Time to send briefing, e.g. 07:00")
    briefing_enabled: bool = Field(..., description="Whether briefing is enabled")


@router.patch("/{milo_id}/autonomy", response_model=MiloResponse)
def update_milo_autonomy(
    request: Request,
    milo_id: str,
    payload: AutonomyUpdateRequest
):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = context.tenant_id
    user_id = context.sub
    # Verify user is owner/admin
    stmt = select(Membership).where(
        Membership.tenant_id == uuid.UUID(tenant_id),
        Membership.user_id == uuid.UUID(user_id)
    )
    membership = db.scalars(stmt).first()
    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owner or admin can update autonomy levels")

    milo = db.get(Milo, uuid.UUID(milo_id))
    if not milo or str(milo.tenant_id) != tenant_id:
        raise HTTPException(status_code=404, detail="Milo not found")

    restricted_tools = ["sms.send", "esign.send", "quickbooks.write"]
    valid_levels = ["draft", "copilot", "auto"]

    for tool_class, level in payload.autonomy_levels.items():
        if level not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid autonomy level: {level}")
        if level == "auto" and tool_class in restricted_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Tool class {tool_class} cannot be set to 'auto'"
            )

    milo.autonomy_levels = payload.autonomy_levels
    db.commit()
    db.refresh(milo)

    return MiloResponse(
        id=str(milo.id),
        name=milo.name,
        persona_pack=milo.persona_pack,
        autonomy_levels=milo.autonomy_levels,
        briefing_send_time=milo.briefing_send_time,
        briefing_enabled=milo.briefing_enabled
    )

@router.patch("/{milo_id}/briefing", response_model=MiloResponse)
def update_milo_briefing(
    request: Request,
    milo_id: str,
    payload: UpdateBriefingRequest
):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = context.tenant_id
    user_id = context.sub
    
    # Verify user is owner/admin
    stmt = select(Membership).where(
        Membership.tenant_id == uuid.UUID(tenant_id),
        Membership.user_id == uuid.UUID(user_id)
    )
    membership = db.scalars(stmt).first()
    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owner or admin can update briefing settings")

    milo = db.get(Milo, uuid.UUID(milo_id))
    if not milo or str(milo.tenant_id) != tenant_id:
        raise HTTPException(status_code=404, detail="Milo not found")

    milo.briefing_send_time = payload.briefing_send_time
    milo.briefing_enabled = payload.briefing_enabled
    db.commit()
    db.refresh(milo)

    # Sync with EventBridge Scheduler
    try:
        scheduler_client = boto3.client('scheduler', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        schedule_name = f"milo-briefing-{tenant_id}"
        
        # Get the primary user to find timezone
        owner_membership = db.scalars(select(Membership).where(
            Membership.tenant_id == uuid.UUID(tenant_id),
            Membership.role == "owner"
        )).first()
        
        timezone = "UTC"
        if owner_membership:
            owner = db.get(User, owner_membership.user_id)
            if owner and owner.tz:
                timezone = owner.tz
                
        hour, minute = payload.briefing_send_time.split(":")
        cron_expr = f"cron({minute} {hour} * * ? *)"
        
        lambda_arn = os.environ.get("BRIEFING_LAMBDA_ARN")
        role_arn = os.environ.get("SCHEDULER_ROLE_ARN")
        
        if lambda_arn and role_arn:
            if payload.briefing_enabled:
                try:
                    scheduler_client.create_schedule(
                        Name=schedule_name,
                        ScheduleExpression=cron_expr,
                        ScheduleExpressionTimezone=timezone,
                        FlexibleTimeWindow={'Mode': 'OFF'},
                        State='ENABLED',
                        Target={
                            'Arn': lambda_arn,
                            'RoleArn': role_arn,
                            'Input': json.dumps({"tenant_id": tenant_id})
                        }
                    )
                except scheduler_client.exceptions.ConflictException:
                    scheduler_client.update_schedule(
                        Name=schedule_name,
                        ScheduleExpression=cron_expr,
                        ScheduleExpressionTimezone=timezone,
                        FlexibleTimeWindow={'Mode': 'OFF'},
                        State='ENABLED',
                        Target={
                            'Arn': lambda_arn,
                            'RoleArn': role_arn,
                            'Input': json.dumps({"tenant_id": tenant_id})
                        }
                    )
            else:
                try:
                    scheduler_client.update_schedule(
                        Name=schedule_name,
                        ScheduleExpression=cron_expr,
                        ScheduleExpressionTimezone=timezone,
                        FlexibleTimeWindow={'Mode': 'OFF'},
                        State='DISABLED',
                        Target={
                            'Arn': lambda_arn,
                            'RoleArn': role_arn,
                            'Input': json.dumps({"tenant_id": tenant_id})
                        }
                    )
                except scheduler_client.exceptions.ResourceNotFoundException:
                    pass # Nothing to disable
    except Exception as e:
        # We don't want to fail the API request if scheduler sync fails in dev
        import logging
        logging.getLogger(__name__).error(f"Failed to sync schedule: {e}")

    return MiloResponse(
        id=str(milo.id),
        name=milo.name,
        persona_pack=milo.persona_pack,
        autonomy_levels=milo.autonomy_levels,
        briefing_send_time=milo.briefing_send_time,
        briefing_enabled=milo.briefing_enabled
    )
