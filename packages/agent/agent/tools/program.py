import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models.program import Decision, Milestone, Program, Risk, Task
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class ProgramReadInput(BaseModel):
    program_id: str | None = Field(default=None, description="The ID of the program to read. If null, returns all active programs.")
    include_details: bool = Field(default=False, description="If true, include milestones, tasks, risks, and decisions.")


class ProgramReadOutput(BaseModel):
    programs: list[dict[str, Any]]


class ProgramReadTool(Tool):
    name = "program.read"
    description = "Read structured program data including milestones, tasks, risks, and decisions."
    input_schema = ProgramReadInput
    output_schema = ProgramReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        program_id_str = input_data.get("program_id")
        include_details = input_data.get("include_details", False)

        stmt = select(Program).where(Program.tenant_id == uuid.UUID(context.tenant_id))
        
        if program_id_str:
            stmt = stmt.where(Program.id == uuid.UUID(program_id_str))
            
        programs = context.session.scalars(stmt).all()

        results = []
        for p in programs:
            data = {
                "id": str(p.id),
                "name": p.name,
                "status": p.status,
                "charter": p.charter,
                "success_criteria": p.success_criteria
            }
            if include_details:
                # Load milestones
                m_stmt = select(Milestone).where(Milestone.program_id == p.id)
                data["milestones"] = [{"id": str(m.id), "name": m.name, "status": m.status} for m in context.session.scalars(m_stmt).all()]
                
                # Load tasks
                t_stmt = select(Task).where(Task.program_id == p.id)
                data["tasks"] = [{"id": str(t.id), "title": t.title, "status": t.status} for t in context.session.scalars(t_stmt).all()]

                # Load risks
                r_stmt = select(Risk).where(Risk.program_id == p.id)
                data["risks"] = [{"id": str(r.id), "title": r.title, "status": r.status, "likelihood": r.likelihood, "impact": r.impact} for r in context.session.scalars(r_stmt).all()]

            results.append(data)

        return ProgramReadOutput(programs=results).model_dump()


class ProgramUpdateInput(BaseModel):
    entity_type: Literal["program", "milestone", "task", "risk", "decision"] = Field(description="The type of entity to update")
    entity_id: str | None = Field(default=None, description="The ID of the entity to update. If null, a new entity is created.")
    program_id: str | None = Field(default=None, description="The ID of the program (required for creating child entities).")
    payload: dict[str, Any] = Field(description="The fields to update or create")


class ProgramUpdateOutput(BaseModel):
    id: str = Field(description="The ID of the updated or created entity")


class ProgramUpdateTool(Tool):
    name = "program.update"
    description = "Update or create program, milestone, task, risk, or decision entities."
    input_schema = ProgramUpdateInput
    output_schema = ProgramUpdateOutput
    mutates = True
    requires_approval = False # Dynamic gating can be added at the runner layer for financial fields

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        entity_type = input_data["entity_type"]
        entity_id_str = input_data.get("entity_id")
        program_id_str = input_data.get("program_id")
        payload = input_data["payload"]

        entity_class_map = {
            "program": Program,
            "milestone": Milestone,
            "task": Task,
            "risk": Risk,
            "decision": Decision
        }
        
        EntityClass = entity_class_map[entity_type]
        entity = None
        
        if entity_id_str:
            entity = context.session.get(EntityClass, uuid.UUID(entity_id_str))
            if not entity:
                raise ValueError(f"{entity_type} with ID {entity_id_str} not found.")
        else:
            entity = EntityClass(tenant_id=uuid.UUID(context.tenant_id))
            if entity_type != "program":
                if not program_id_str:
                    raise ValueError("program_id is required when creating a child entity.")
                entity.program_id = uuid.UUID(program_id_str)
            context.session.add(entity)

        # Update fields
        for key, value in payload.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        context.session.commit()

        return ProgramUpdateOutput(id=str(entity.id)).model_dump()
