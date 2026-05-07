import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.program import Program

router = APIRouter(prefix="/v1/programs", tags=["programs"])


class ProgramCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the program")
    charter: dict[str, Any] | None = None
    success_criteria: dict[str, Any] | None = None


class ProgramResponse(BaseModel):
    id: str
    name: str
    status: str
    charter: dict[str, Any] | None
    success_criteria: dict[str, Any] | None


@router.get("", response_model=list[ProgramResponse])
def get_programs(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = context.tenant_id
    stmt = select(Program).where(Program.tenant_id == uuid.UUID(tenant_id))
    programs = db.scalars(stmt).all()
    return [
        ProgramResponse(
            id=str(p.id),
            name=p.name,
            status=p.status,
            charter=p.charter,
            success_criteria=p.success_criteria
        ) for p in programs
    ]


@router.post("", response_model=ProgramResponse)
def create_program(request: Request, payload: ProgramCreateRequest):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = context.tenant_id
    program = Program(
        tenant_id=uuid.UUID(tenant_id),
        name=payload.name,
        charter=payload.charter,
        success_criteria=payload.success_criteria,
        status="initiating"
    )
    db.add(program)
    db.commit()
    db.refresh(program)

    return ProgramResponse(
        id=str(program.id),
        name=program.name,
        status=program.status,
        charter=program.charter,
        success_criteria=program.success_criteria
    )
