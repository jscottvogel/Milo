import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models.program import Decision, Risk, WorkItem, ChangeRequest, Stakeholder, Commitment
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class WorkItemReadInput(BaseModel):
    item_id: str | None = Field(default=None, description="The ID of the work item to read. If null, returns root items.")
    include_children: bool = Field(default=False, description="If true, include all child work items, risks, decisions, and change_requests.")


class WorkItemReadOutput(BaseModel):
    items: list[dict[str, Any]]


class WorkItemReadTool(Tool):
    name = "work_item.read"
    description = "Read structured work item data including the 8-layer hierarchy, risks, decisions, and change requests."
    input_schema = WorkItemReadInput
    output_schema = WorkItemReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        item_id_str = input_data.get("item_id")
        include_children = input_data.get("include_children", False)

        stmt = select(WorkItem).where(WorkItem.tenant_id == uuid.UUID(context.tenant_id))
        
        if item_id_str:
            stmt = stmt.where(WorkItem.id == uuid.UUID(item_id_str))
        else:
            stmt = stmt.where(WorkItem.parent_id == None)
            
        items = context.session.scalars(stmt).all()

        results = []
        for w in items:
            data = {
                "id": str(w.id),
                "name": w.name,
                "item_type": w.item_type,
                "status": w.status,
                "description": w.description
            }
            if include_children:
                # Fetch children
                c_stmt = select(WorkItem).where(WorkItem.parent_id == w.id)
                data["children"] = [{"id": str(c.id), "name": c.name, "item_type": c.item_type, "status": c.status} for c in context.session.scalars(c_stmt).all()]

                # Load risks
                r_stmt = select(Risk).where(Risk.work_item_id == w.id)
                data["risks"] = [{"id": str(r.id), "title": r.title, "status": r.status, "likelihood": r.likelihood, "impact": r.impact} for r in context.session.scalars(r_stmt).all()]

                # Load change requests
                cr_stmt = select(ChangeRequest).where(ChangeRequest.work_item_id == w.id)
                data["change_requests"] = [{"id": str(cr.id), "title": cr.title, "status": cr.status, "reason": cr.reason, "impact_analysis": cr.impact_analysis} for cr in context.session.scalars(cr_stmt).all()]

                # Load decisions
                d_stmt = select(Decision).where(Decision.work_item_id == w.id)
                data["decisions"] = [{"id": str(d.id), "title": d.title, "decision_text": d.decision_text, "alternatives_jsonb": d.alternatives_jsonb, "source_link": d.source_link} for d in context.session.scalars(d_stmt).all()]

                # Load stakeholders
                sh_stmt = select(Stakeholder).where(Stakeholder.work_item_id == w.id)
                data["stakeholders"] = [{"id": str(sh.id), "name": sh.name, "email": sh.email, "role": sh.role, "influence": sh.influence, "interest": sh.interest, "satisfaction": sh.satisfaction, "notes": sh.notes} for sh in context.session.scalars(sh_stmt).all()]

                # Load action items (commitments)
                ci_stmt = select(Commitment).where(Commitment.work_item_id == w.id)
                data["action_items"] = [{"id": str(ci.id), "description": ci.description, "owner_name": ci.owner_name, "due_date": ci.due_date.isoformat() if ci.due_date else None, "status": ci.status} for ci in context.session.scalars(ci_stmt).all()]

            results.append(data)

        return WorkItemReadOutput(items=results).model_dump()


class WorkItemUpdateInput(BaseModel):
    entity_type: Literal["objective", "outcome", "key_result", "initiative", "project", "workstream", "milestone", "task", "risk", "decision", "change_request", "stakeholder", "action_item"] = Field(description="The type of entity to update")
    entity_id: str | None = Field(default=None, description="The ID of the entity to update. If null, a new entity is created.")
    parent_id: str | None = Field(default=None, description="The ID of the parent work item (required for creating child entities).")
    payload: dict[str, Any] = Field(description="The fields to update or create. For work items: name, description, status, start_date (ISO), due_date (ISO), owner_name, metadata_json (use this to store financial time-series data using key 'financials' containing an array of objects like {\"period\": \"YYYY-MM\", \"budget\": 100, \"actual\": 50}), dependencies (list of strings representing names of entities this depends on). For risk: title, likelihood (int 1-5), impact (int 1-5), status, mitigation. For change_request: title, description, reason, status, impact_analysis. For decision: title, decision_text, alternatives_jsonb (dict), source_link. For stakeholder: name, role (use 'sponsor' if applicable), email, influence, interest, notes, satisfaction. For action_item: description, owner_name, due_date (ISO), status (pending/met/missed).")


class WorkItemUpdateOutput(BaseModel):
    id: str = Field(description="The ID of the updated or created entity")


class WorkItemUpdateTool(Tool):
    name = "work_item.update"
    description = "Update or create objectives, outcomes, key_results, initiatives, projects, workstreams, milestones, tasks, risks, decisions, or change_requests."
    input_schema = WorkItemUpdateInput
    output_schema = WorkItemUpdateOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        entity_type = input_data["entity_type"]
        entity_id_str = input_data.get("entity_id")
        parent_id_str = input_data.get("parent_id")
        payload = input_data["payload"]
        
        is_work_item = entity_type not in ["risk", "decision", "change_request", "stakeholder", "action_item"]

        EntityClass = WorkItem if is_work_item else (Risk if entity_type == "risk" else (Decision if entity_type == "decision" else (ChangeRequest if entity_type == "change_request" else (Stakeholder if entity_type == "stakeholder" else Commitment))))
        entity = None
        
        if entity_id_str:
            entity = context.session.get(EntityClass, uuid.UUID(entity_id_str))
            if not entity:
                raise ValueError(f"{entity_type} with ID {entity_id_str} not found.")
        else:
            # Idempotent Upsert Logic: Check if entity already exists
            parent_uuid = uuid.UUID(parent_id_str) if parent_id_str else None
            stmt = select(EntityClass).where(EntityClass.tenant_id == uuid.UUID(context.tenant_id))
            
            if is_work_item:
                stmt = stmt.where(
                    EntityClass.item_type == entity_type,
                    EntityClass.name == payload.get("name", ""),
                    EntityClass.parent_id == parent_uuid
                )
            else:
                stmt = stmt.where(EntityClass.work_item_id == parent_uuid)
                if entity_type in ["risk", "decision", "change_request"]:
                    stmt = stmt.where(EntityClass.title == payload.get("title", ""))
                elif entity_type == "stakeholder":
                    stmt = stmt.where(EntityClass.name == payload.get("name", ""))
                elif entity_type == "action_item":
                    stmt = stmt.where(EntityClass.description == payload.get("description", ""))

            existing_entity = context.session.scalar(stmt)
            if existing_entity:
                entity = existing_entity
            else:
                entity = EntityClass(tenant_id=uuid.UUID(context.tenant_id))
                if is_work_item:
                    entity.item_type = entity_type
                    entity.parent_id = parent_uuid
                else:
                    if not parent_id_str:
                        raise ValueError(f"parent_id (work_item_id) is required when creating a {entity_type}.")
                    entity.work_item_id = parent_uuid
                context.session.add(entity)

        # Handle date parsing and dependencies
        for key, value in payload.items():
            if key in ["start_date", "target_date", "due_date", "actual_date"] and value:
                from dateutil import parser
                try:
                    parsed_date = parser.parse(value)
                    setattr(entity, key, parsed_date.replace(tzinfo=None))
                except Exception:
                    pass
            elif key == "dependencies" and isinstance(value, list) and parent_id_str:
                dep_ids = []
                for dep_name in value:
                    if not isinstance(dep_name, str): continue
                    dep = context.session.scalar(select(WorkItem).where(WorkItem.parent_id == uuid.UUID(parent_id_str), WorkItem.name == dep_name))
                    if dep:
                        dep_ids.append(str(dep.id))
                setattr(entity, key, dep_ids)
            elif key == "metadata_json" and isinstance(value, dict):
                # Merge metadata to preserve existing fields like source_document
                existing_meta = getattr(entity, "metadata_json", {}) or {}
                # Create a new dict to ensure SQLAlchemy detects the change
                new_meta = dict(existing_meta)
                new_meta.update(value)
                setattr(entity, "metadata_json", new_meta)
            elif hasattr(entity, key):
                setattr(entity, key, value)

        context.session.commit()

        return WorkItemUpdateOutput(id=str(entity.id)).model_dump()
