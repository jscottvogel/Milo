import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.middleware.tenant_context import get_db
from db.models.identity import Milo, User, Membership

# Assuming we have a get_current_user_id and get_current_tenant_id function.
# For PoC Phase 5, we'll reuse the mock dependencies from approvals.py or similar.
def get_current_tenant_id() -> str:
    return "00000000-0000-0000-0000-000000000001"  # Mock

def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"  # Mock

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
    milo_id: str,
    request: AutonomyUpdateRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id)
):
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

    for tool_class, level in request.autonomy_levels.items():
        if level not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid autonomy level: {level}")
        if level == "auto" and tool_class in restricted_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Tool class {tool_class} cannot be set to 'auto'"
            )

    milo.autonomy_levels = request.autonomy_levels
    db.commit()
    db.refresh(milo)

    return MiloResponse(
        id=str(milo.id),
        name=milo.name,
        persona_pack=milo.persona_pack,
        autonomy_levels=milo.autonomy_levels
    )
