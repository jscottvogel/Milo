import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.identity import Milo, User, Membership

router = APIRouter(prefix="/v1/milos", tags=["milos"])


class AutonomyUpdateRequest(BaseModel):
    autonomy_levels: dict[str, str] = Field(..., description="Map of tool class to autonomy level (draft, copilot, auto)")


class MiloResponse(BaseModel):
    id: str
    name: str
    persona_pack: str
    autonomy_levels: dict[str, str]


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
        autonomy_levels=milo.autonomy_levels
    )
