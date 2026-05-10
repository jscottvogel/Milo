import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models.program import WorkItem, Risk, Decision, ChangeRequest, ProgramStakeholder, Commitment
from fastapi import BackgroundTasks
import asyncio
import json
import boto3
import os
from sqlalchemy import create_engine
from agent.tools.registry import registry
from agent.tools.context import AgentContext

router = APIRouter(prefix="/v1/work_items", tags=["work_items"])

class WorkItemCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the work item")
    item_type: str = Field(..., description="objective, outcome, key_result, initiative, project, workstream, milestone, task")
    parent_id: str | None = None
    description: str | None = None

class WorkItemResponse(BaseModel):
    id: str
    name: str
    item_type: str
    status: str
    parent_id: str | None = None
    description: str | None = None
    owner_name: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    actual_date: str | None = None
    metadata_json: dict | None = None
    dependencies: list[str] | None = None

class RiskResponse(BaseModel):
    id: str
    work_item_id: str | None = None
    title: str
    status: str
    likelihood: int
    impact: int

class ChangeRequestResponse(BaseModel):
    id: str
    work_item_id: str | None = None
    title: str
    description: str
    reason: str | None = None
    status: str
    impact_analysis: str | None = None

class DecisionResponse(BaseModel):
    id: str
    work_item_id: str | None = None
    title: str
    decision_text: str
    alternatives_jsonb: dict | None = None
    source_link: str | None = None

class StakeholderResponse(BaseModel):
    id: str
    work_item_id: str | None = None
    name: str
    email: str | None = None
    role: str | None = None
    influence: str | None = None
    interest: str | None = None
    satisfaction: str | None = None
    notes: str | None = None

class ActionItemResponse(BaseModel):
    id: str
    work_item_id: str | None = None
    description: str
    owner_name: str | None = None
    due_date: str | None = None
    status: str

class DashboardResponse(BaseModel):
    root_items: list[WorkItemResponse]
    next_up: list[WorkItemResponse]
    recently_completed: list[WorkItemResponse]
    high_risks: list[RiskResponse]

class WorkItemTreeResponse(WorkItemResponse):
    children: list["WorkItemTreeResponse"] = []
    risks: list[RiskResponse] = []
    change_requests: list[ChangeRequestResponse] = []
    decisions: list[DecisionResponse] = []
    stakeholders: list[StakeholderResponse] = []
    action_items: list[ActionItemResponse] = []

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = uuid.UUID(context.tenant_id)
    
    # 1. Root Items (Objectives or Initiatives depending on what's active)
    # Let's fetch all top-level items (parent_id is NULL)
    root_items_db = db.scalars(select(WorkItem).where(WorkItem.tenant_id == tenant_id, WorkItem.parent_id == None, WorkItem.status != 'closed')).all()
    root_items = [
        WorkItemResponse(
            id=str(w.id), name=w.name, item_type=w.item_type, status=w.status,
            description=w.description, owner_name=w.owner_name,
            start_date=w.start_date.isoformat() if w.start_date else None,
            due_date=w.due_date.isoformat() if w.due_date else None,
            metadata_json=w.metadata_json
        ) for w in root_items_db
    ]
    
    all_tasks = db.scalars(select(WorkItem).where(WorkItem.tenant_id == tenant_id, WorkItem.item_type == 'task')).all()
    all_risks = db.scalars(select(Risk).where(Risk.tenant_id == tenant_id)).all()
        
    # 2. Next Up (Tasks)
    next_up_tasks = [t for t in all_tasks if t.status in ('todo', 'in_progress', 'pending')]
    next_up_tasks.sort(key=lambda x: x.due_date.timestamp() if x.due_date else float('inf'))
    next_up = []
    for t in next_up_tasks[:5]:
        next_up.append(WorkItemResponse(
            id=str(t.id), name=t.name, item_type=t.item_type, status=t.status,
            parent_id=str(t.parent_id) if t.parent_id else None,
            description=t.description, owner_name=t.owner_name,
            due_date=t.due_date.isoformat() if t.due_date else None
        ))
        
    # 3. Recently Completed (Tasks)
    completed_tasks = [t for t in all_tasks if t.status in ('done', 'completed')]
    completed_tasks.sort(key=lambda x: x.due_date.timestamp() if x.due_date else 0, reverse=True)
    recently_completed = []
    for t in completed_tasks[:5]:
        recently_completed.append(WorkItemResponse(
            id=str(t.id), name=t.name, item_type=t.item_type, status=t.status,
            parent_id=str(t.parent_id) if t.parent_id else None,
            description=t.description, owner_name=t.owner_name,
            due_date=t.due_date.isoformat() if t.due_date else None
        ))
        
    # 4. High Risks
    critical_risks = [r for r in all_risks if r.status != 'closed' and (r.impact >= 4 or r.likelihood >= 4)]
    critical_risks.sort(key=lambda x: x.impact * x.likelihood, reverse=True)
    high_risks = []
    for r in critical_risks[:5]:
        high_risks.append(RiskResponse(
            id=str(r.id),
            work_item_id=str(r.work_item_id) if r.work_item_id else None,
            title=r.title,
            status=r.status,
            likelihood=r.likelihood,
            impact=r.impact
        ))

    return DashboardResponse(
        root_items=root_items,
        next_up=next_up,
        recently_completed=recently_completed,
        high_risks=high_risks
    )


def build_tree(items: list[WorkItem], parent_id: uuid.UUID | None, all_risks: list[Risk] | None = None, all_crs: list[ChangeRequest] | None = None, all_decisions: list[Decision] | None = None, all_stakeholders: list[ProgramStakeholder] | None = None, all_action_items: list[Commitment] | None = None) -> list[WorkItemTreeResponse]:
    if all_risks is None: all_risks = []
    if all_crs is None: all_crs = []
    if all_decisions is None: all_decisions = []
    if all_stakeholders is None: all_stakeholders = []
    if all_action_items is None: all_action_items = []
    
    tree = []
    for item in items:
        if item.parent_id == parent_id:
            node_risks = [
                RiskResponse(
                    id=str(r.id), work_item_id=str(r.work_item_id) if r.work_item_id else None,
                    title=r.title, status=r.status, likelihood=r.likelihood, impact=r.impact
                ) for r in all_risks if r.work_item_id == item.id
            ]
            node_crs = [
                ChangeRequestResponse(
                    id=str(cr.id), work_item_id=str(cr.work_item_id) if cr.work_item_id else None,
                    title=cr.title, description=cr.description, reason=cr.reason, status=cr.status, impact_analysis=cr.impact_analysis
                ) for cr in all_crs if cr.work_item_id == item.id
            ]
            node_decisions = [
                DecisionResponse(
                    id=str(d.id), work_item_id=str(d.work_item_id) if d.work_item_id else None,
                    title=d.title, decision_text=d.decision_text, alternatives_jsonb=d.alternatives_jsonb, source_link=d.source_link
                ) for d in all_decisions if d.work_item_id == item.id
            ]
            node_stakeholders = [
                StakeholderResponse(
                    id=str(sh.stakeholder_sub), work_item_id=str(sh.program_id) if sh.program_id else None,
                    name=sh.profile.full_name if sh.profile else "Unknown", email=None, role=sh.role, influence=sh.influence, interest=sh.interest, satisfaction=sh.satisfaction, notes=None
                ) for sh in all_stakeholders if sh.program_id == item.id
            ]
            node_action_items = [
                ActionItemResponse(
                    id=str(ci.id), work_item_id=str(ci.work_item_id) if ci.work_item_id else None,
                    description=ci.description, owner_name=ci.owner_name, due_date=ci.due_date.isoformat() if ci.due_date else None, status=ci.status
                ) for ci in all_action_items if ci.work_item_id == item.id
            ]
            children_nodes = build_tree(items, item.id, all_risks, all_crs, all_decisions, all_stakeholders, all_action_items)
            
            # Auto-compute status from children
            computed_status = item.status
            if children_nodes:
                if any(c.status in ('blocked', 'red') for c in children_nodes):
                    computed_status = 'blocked'
                elif any(c.status in ('at_risk', 'amber') for c in children_nodes):
                    computed_status = 'at_risk'
                elif all(c.status in ('done', 'completed') for c in children_nodes):
                    computed_status = 'done'
                else:
                    computed_status = 'in_progress'

            node = WorkItemTreeResponse(
                id=str(item.id),
                name=item.name,
                item_type=item.item_type,
                status=computed_status,
                parent_id=str(item.parent_id) if item.parent_id else None,
                description=item.description,
                owner_name=item.owner_name,
                start_date=item.start_date.isoformat() if item.start_date else None,
                due_date=item.due_date.isoformat() if item.due_date else None,
                metadata_json=item.metadata_json,
                dependencies=[str(d) for d in item.dependencies] if item.dependencies else [],
                children=children_nodes,
                risks=node_risks,
                change_requests=node_crs,
                decisions=node_decisions,
                stakeholders=node_stakeholders,
                action_items=node_action_items
            )
            tree.append(node)
    return tree

@router.get("/tree", response_model=list[WorkItemTreeResponse])
def get_full_tree(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session missing")
    
    tenant_id = uuid.UUID(context.tenant_id)
    all_items = db.scalars(select(WorkItem).where(WorkItem.tenant_id == tenant_id)).all()
    all_risks = db.scalars(select(Risk).where(Risk.tenant_id == tenant_id)).all()
    all_crs = db.scalars(select(ChangeRequest).where(ChangeRequest.tenant_id == tenant_id)).all()
    all_decisions = db.scalars(select(Decision).where(Decision.tenant_id == tenant_id)).all()
    all_stakeholders = db.scalars(select(ProgramStakeholder).where(ProgramStakeholder.tenant_id == tenant_id)).all()
    all_action_items = db.scalars(select(Commitment).where(Commitment.tenant_id == tenant_id)).all()
    
    return build_tree(all_items, None, all_risks, all_crs, all_decisions, all_stakeholders, all_action_items)

@router.get("/validation-errors")
def get_validation_errors(request: Request):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session missing")
        
    tenant_id = uuid.UUID(context.tenant_id)
    items = db.scalars(select(WorkItem).where(WorkItem.tenant_id == tenant_id, WorkItem.status != 'archived')).all()
    risks = db.scalars(select(Risk).where(Risk.tenant_id == tenant_id, Risk.status != 'archived')).all()
    decisions = db.scalars(select(Decision).where(Decision.tenant_id == tenant_id)).all()
    
    id_to_type = {str(i.id): i.item_type for i in items}
    
    errors = []
    
    for i in items:
        p_type = id_to_type.get(str(i.parent_id)) if i.parent_id else None
        
        if i.item_type in ["key_result", "initiative"]:
            if p_type not in ["outcome", "objective"]:
                errors.append(f"Linkage Error: {i.item_type} '{i.name}' has parent of type {p_type} (expected outcome or objective)")
        elif i.item_type == "project":
            if p_type != "initiative":
                errors.append(f"Linkage Error: project '{i.name}' has parent of type {p_type} (expected initiative)")
        elif i.item_type == "workstream":
            if p_type not in ["project", "initiative"]:
                errors.append(f"Linkage Error: workstream '{i.name}' has parent of type {p_type} (expected project or initiative)")
        elif i.item_type == "milestone":
            if p_type not in ["workstream", "project"]:
                errors.append(f"Linkage Error: milestone '{i.name}' has parent of type {p_type} (expected workstream or project)")
        elif i.item_type == "task":
            if p_type not in ["milestone", "workstream"]:
                errors.append(f"Linkage Error: task '{i.name}' has parent of type {p_type} (expected milestone or workstream)")
                
    for r in risks:
        p_type = id_to_type.get(str(r.work_item_id)) if r.work_item_id else None
        if p_type not in ["project", "initiative"]:
            errors.append(f"Linkage Error: risk '{r.title}' has parent of type {p_type} (expected project or initiative)")
            
    for d in decisions:
        p_type = id_to_type.get(str(d.work_item_id)) if d.work_item_id else None
        if p_type not in ["project", "initiative"]:
            errors.append(f"Linkage Error: decision '{d.title}' has parent of type {p_type} (expected project or initiative)")

    return {"errors": errors}

@router.get("/{item_id}", response_model=WorkItemTreeResponse)
def get_work_item_details(request: Request, item_id: str):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session missing")
    
    tenant_id = context.tenant_id
    try:
        pid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
        
    stmt = select(WorkItem).where(WorkItem.tenant_id == uuid.UUID(tenant_id), WorkItem.id == pid)
    item = db.scalar(stmt)
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")
        
    all_items = db.scalars(select(WorkItem).where(WorkItem.tenant_id == uuid.UUID(tenant_id))).all()
    all_risks = db.scalars(select(Risk).where(Risk.tenant_id == uuid.UUID(tenant_id))).all()
    all_crs = db.scalars(select(ChangeRequest).where(ChangeRequest.tenant_id == uuid.UUID(tenant_id))).all()
    all_decisions = db.scalars(select(Decision).where(Decision.tenant_id == uuid.UUID(tenant_id))).all()
    all_stakeholders = db.scalars(select(ProgramStakeholder).where(ProgramStakeholder.tenant_id == uuid.UUID(tenant_id))).all()
    all_action_items = db.scalars(select(Commitment).where(Commitment.tenant_id == uuid.UUID(tenant_id))).all()

    root_risks = [
        RiskResponse(
            id=str(r.id), work_item_id=str(r.work_item_id) if r.work_item_id else None,
            title=r.title, status=r.status, likelihood=r.likelihood, impact=r.impact
        ) for r in all_risks if r.work_item_id == item.id
    ]
    root_crs = [
        ChangeRequestResponse(
            id=str(cr.id), work_item_id=str(cr.work_item_id) if cr.work_item_id else None,
            title=cr.title, description=cr.description, reason=cr.reason, status=cr.status, impact_analysis=cr.impact_analysis
        ) for cr in all_crs if cr.work_item_id == item.id
    ]
    root_decisions = [
        DecisionResponse(
            id=str(d.id), work_item_id=str(d.work_item_id) if d.work_item_id else None,
            title=d.title, decision_text=d.decision_text, alternatives_jsonb=d.alternatives_jsonb, source_link=d.source_link
        ) for d in all_decisions if d.work_item_id == item.id
    ]
    root_stakeholders = [
        StakeholderResponse(
            id=str(sh.stakeholder_sub), work_item_id=str(sh.program_id) if sh.program_id else None,
            name=sh.profile.full_name if sh.profile else "Unknown", email=None, role=sh.role, influence=sh.influence, interest=sh.interest, satisfaction=sh.satisfaction, notes=None
        ) for sh in all_stakeholders if sh.program_id == item.id
    ]
    root_action_items = [
        ActionItemResponse(
            id=str(ci.id), work_item_id=str(ci.work_item_id) if ci.work_item_id else None,
            description=ci.description, owner_name=ci.owner_name, due_date=ci.due_date.isoformat() if ci.due_date else None, status=ci.status
        ) for ci in all_action_items if ci.work_item_id == item.id
    ]
    
    return WorkItemTreeResponse(
        id=str(item.id),
        name=item.name,
        item_type=item.item_type,
        status=item.status,
        parent_id=str(item.parent_id) if item.parent_id else None,
        description=item.description,
        owner_name=item.owner_name,
        start_date=item.start_date.isoformat() if item.start_date else None,
        due_date=item.due_date.isoformat() if item.due_date else None,
        metadata_json=item.metadata_json,
        dependencies=[str(d) for d in item.dependencies] if item.dependencies else [],
        children=build_tree(all_items, item.id, all_risks, all_crs, all_decisions, all_stakeholders, all_action_items),
        risks=root_risks,
        change_requests=root_crs,
        decisions=root_decisions,
        stakeholders=root_stakeholders,
        action_items=root_action_items
    )

@router.post("", response_model=WorkItemResponse)
def create_work_item(request: Request, payload: WorkItemCreateRequest):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session missing")
        
    tenant_id = context.tenant_id
    parent_uuid = uuid.UUID(payload.parent_id) if payload.parent_id else None
    
    item = WorkItem(
        tenant_id=uuid.UUID(tenant_id),
        name=payload.name,
        item_type=payload.item_type,
        status="pending",
        parent_id=parent_uuid,
        description=payload.description
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return WorkItemResponse(
        id=str(item.id),
        name=item.name,
        item_type=item.item_type,
        status=item.status,
        parent_id=str(item.parent_id) if item.parent_id else None,
        description=item.description
    )

import os
import boto3

class ArtifactResponse(BaseModel):
    key: str
    filename: str
    size: int
    last_modified: str
    url: str | None = None

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str

class PresignedUrlResponse(BaseModel):
    upload_url: str
    key: str

@router.get("/{item_id}/artifacts", response_model=list[ArtifactResponse])
def list_artifacts(request: Request, item_id: str):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = context.tenant_id
    bucket = os.environ.get("S3_BUCKET_NAME", "milo-artifacts-poc")
    prefix = f"{tenant_id}/work_items/{item_id}/"
    
    s3 = boto3.client('s3')
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    except Exception as e:
        return []

    artifacts = []
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('/'): continue # skip folder markers
            filename = key.replace(prefix, "")
            
            # Generate a presigned GET url for downloading
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=3600
            )
            
            artifacts.append(ArtifactResponse(
                key=key,
                filename=filename,
                size=obj['Size'],
                last_modified=obj['LastModified'].isoformat(),
                url=url
            ))
            
    return artifacts

@router.post("/{item_id}/artifacts/upload_url", response_model=PresignedUrlResponse)
def get_upload_url(request: Request, item_id: str, payload: PresignedUrlRequest):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    tenant_id = context.tenant_id
    bucket = os.environ.get("S3_BUCKET_NAME", "milo-artifacts-poc")
    
    import time
    safe_filename = "".join(c for c in payload.filename if c.isalnum() or c in "._- ")
    key = f"{tenant_id}/work_items/{item_id}/{int(time.time())}_{safe_filename}"
    
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket, 'Key': key, 'ContentType': payload.content_type},
        ExpiresIn=3600
    )
    return PresignedUrlResponse(upload_url=url, key=key)


async def run_reconciliation_task(run_id: str, tenant_id: str):
    bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
    s3 = boto3.client("s3")
    diff_key = f"{tenant_id}/hydration_runs/{run_id}/diff.json"
    manifest_key = f"{tenant_id}/hydration_runs/{run_id}/manifest.json"
    log_key = f"{tenant_id}/hydration_runs/{run_id}/reconciliation_log.json"
    
    loop = asyncio.get_running_loop()
    try:
        diff_obj = await loop.run_in_executor(None, lambda: s3.get_object(Bucket=bucket, Key=diff_key))
        diff = json.loads(diff_obj['Body'].read())
        
        man_obj = await loop.run_in_executor(None, lambda: s3.get_object(Bucket=bucket, Key=manifest_key))
        manifest = json.loads(man_obj['Body'].read())
    except Exception as e:
        return
        
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    log = {"status": "running", "archived": 0, "reparented": 0, "created": 0}
    def update_log():
        s3.put_object(Bucket=bucket, Key=log_key, Body=json.dumps(log))
        
    with Session(engine) as db:
        context = AgentContext(session=db, tenant_id=tenant_id, thread_id="", milo_id="", integration_tokens=[])
        update_tool = registry.get_tool("work_item.update")
        
        # 1. Archive
        for a in diff.get("to_archive", []):
            try:
                await update_tool.invoke({
                    "entity_type": a["type"],
                    "entity_id": a["id"],
                    "payload": {"status": "archived"}
                }, context)
                log["archived"] += 1
            except Exception: pass
            
        # 2. Reparent
        # Re-fetch DB to build name_to_id map for reparenting
        db_items = db.scalars(select(WorkItem).where(WorkItem.tenant_id == uuid.UUID(tenant_id))).all()
        name_to_id = {i.name: str(i.id) for i in db_items}
        
        for r in diff.get("to_reparent", []):
            new_p_name = r.get("new_parent")
            new_p_id = name_to_id.get(new_p_name)
            if new_p_id:
                try:
                    await update_tool.invoke({
                        "entity_type": r["type"],
                        "entity_id": r["id"],
                        "parent_id": new_p_id,
                        "payload": {}
                    }, context)
                    log["reparented"] += 1
                except Exception: pass
                
        # 3. Create missing (batch of 5)
        layer_order = ["objective", "outcomes", "key_results", "initiatives", "projects", "workstreams", "milestones", "tasks", "risks", "decisions", "stakeholders"]
        
        async def process_create(layer, item):
            parent_name = item.get("parent")
            parent_id = name_to_id.get(parent_name)
            
            entity_type = layer[:-1] if layer.endswith('s') and layer not in ["risks", "decisions", "stakeholders", "outcomes", "key_results", "projects", "workstreams", "milestones", "tasks"] else layer
            if layer == "objective": entity_type = "objective"
            elif layer == "outcomes": entity_type = "outcome"
            elif layer == "key_results": entity_type = "key_result"
            elif layer == "initiatives": entity_type = "initiative"
            elif layer == "projects": entity_type = "project"
            elif layer == "workstreams": entity_type = "workstream"
            elif layer == "milestones": entity_type = "milestone"
            elif layer == "tasks": entity_type = "task"
            elif layer == "risks": entity_type = "risk"
            elif layer == "decisions": entity_type = "decision"
            elif layer == "stakeholders": entity_type = "stakeholder"
            
            payload = dict(item)
            payload.pop("parent", None)
            
            meta = payload.get("metadata_json", {})
            if "_meta" in manifest:
                meta["source_document"] = manifest["_meta"].get("source_document")
            meta["reconciliation_run_id"] = run_id
            payload["metadata_json"] = meta
            
            try:
                res = await update_tool.invoke({
                    "entity_type": entity_type,
                    "parent_id": parent_id,
                    "payload": payload
                }, context)
                new_id = res["id"] if isinstance(res, dict) else res.id if hasattr(res, "id") else None
                if new_id:
                    name_to_id[payload.get("name") or payload.get("title") or payload.get("description")] = new_id
                log["created"] += 1
                await loop.run_in_executor(None, update_log)
            except Exception as e:
                pass

        to_create = diff.get("to_create", [])
        for layer in layer_order:
            # find all items in to_create that belong to this layer
            # wait, to_create items only have "type", not "layer"
            layer_items = [c for c in to_create if c["type"] == (
                "objective" if layer=="objective" else 
                "outcome" if layer=="outcomes" else 
                "key_result" if layer=="key_results" else 
                "initiative" if layer=="initiatives" else 
                "project" if layer=="projects" else 
                "workstream" if layer=="workstreams" else 
                "milestone" if layer=="milestones" else 
                "task" if layer=="tasks" else 
                "risk" if layer=="risks" else 
                "decision" if layer=="decisions" else 
                "stakeholder" if layer=="stakeholders" else layer
            )]
            
            for i in range(0, len(layer_items), 5):
                batch = layer_items[i:i+5]
                # we need the raw payload from manifest
                raw_items = []
                for b in batch:
                    # locate in manifest
                    man_items = manifest.get(layer, [])
                    if isinstance(man_items, dict): man_items = [man_items]
                    raw_item = next((m for m in man_items if (m.get("name") or m.get("title") or m.get("description")) == b["name"]), b)
                    raw_items.append(raw_item)
                
                tasks = [process_create(layer, r) for r in raw_items]
                await asyncio.gather(*tasks)
                
    log["status"] = "completed"
    await loop.run_in_executor(None, update_log)

@router.post("/reconciliation/{run_id}/execute")
def execute_reconciliation(request: Request, run_id: str, background_tasks: BackgroundTasks):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    background_tasks.add_task(run_reconciliation_task, run_id, str(context.tenant_id))
    return {"status": "started"}

async def run_sequential_hydration(run_id: str, tenant_id: str):
    bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
    s3 = boto3.client("s3")
    manifest_key = f"{tenant_id}/hydration_runs/{run_id}/manifest.json"
    status_key = f"{tenant_id}/hydration_runs/{run_id}/status.json"
    
    status_data = {
        "status": "running", "total_attempted": 0, "total_created": 0,
        "total_failed": 0, "entities": []
    }
    
    def update_status():
        s3.put_object(Bucket=bucket, Key=status_key, Body=json.dumps(status_data))
        
    loop = asyncio.get_running_loop()
    try:
        manifest_obj = await loop.run_in_executor(None, lambda: s3.get_object(Bucket=bucket, Key=manifest_key))
        manifest = json.loads(manifest_obj['Body'].read())
    except Exception as e:
        status_data["status"] = "failed"
        status_data["error"] = f"Failed to load manifest: {e}"
        await loop.run_in_executor(None, update_status)
        return

    await loop.run_in_executor(None, update_status)
    
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    layer_order = ["objective", "outcomes", "key_results", "initiatives", "projects", "workstreams", "milestones", "tasks", "risks", "decisions", "stakeholders"]
    name_to_id = {}
    
    with Session(engine) as db:
        context = AgentContext(session=db, tenant_id=tenant_id, thread_id="", milo_id="", integration_tokens=[])
        update_tool = registry.get_tool("work_item.update")
        if not update_tool:
            status_data["status"] = "failed"
            status_data["error"] = "work_item.update tool not found"
            await loop.run_in_executor(None, update_status)
            return
            
        async def process_entity(layer: str, item: dict):
            status_data["total_attempted"] += 1
            entity_record = {
                "type": layer,
                "name": item.get("name") or item.get("title") or item.get("description") or "Unnamed",
                "status": "pending", "attempt_count": 0, "error": None
            }
            status_data["entities"].append(entity_record)
            await loop.run_in_executor(None, update_status)
            
            parent_id = None
            parent_name = item.get("parent")
            if parent_name and parent_name in name_to_id:
                parent_id = name_to_id[parent_name]
                
            entity_type = layer[:-1] if layer.endswith('s') and layer not in ["risks", "decisions", "stakeholders", "outcomes", "key_results", "projects", "workstreams", "milestones", "tasks"] else layer
            if layer == "objective": entity_type = "objective"
            elif layer == "outcomes": entity_type = "outcome"
            elif layer == "key_results": entity_type = "key_result"
            elif layer == "initiatives": entity_type = "initiative"
            elif layer == "projects": entity_type = "project"
            elif layer == "workstreams": entity_type = "workstream"
            elif layer == "milestones": entity_type = "milestone"
            elif layer == "tasks": entity_type = "task"
            elif layer == "risks": entity_type = "risk"
            elif layer == "decisions": entity_type = "decision"
            elif layer == "stakeholders": entity_type = "stakeholder"
            
            payload = dict(item)
            payload.pop("parent", None)
            
            meta = payload.get("metadata_json", {})
            if "_meta" in manifest:
                meta["source_document"] = manifest["_meta"].get("source_document")
            meta["hydration_run_id"] = run_id
            payload["metadata_json"] = meta
            
            input_data = {
                "entity_type": entity_type,
                "parent_id": parent_id,
                "payload": payload
            }
            
            for attempt in range(1, 4):
                entity_record["attempt_count"] = attempt
                entity_record["status"] = "retrying" if attempt > 1 else "running"
                await loop.run_in_executor(None, update_status)
                try:
                    res = await update_tool.invoke(input_data, context)
                    if isinstance(res, dict) and "error" in res:
                        raise Exception(res["error"])
                    new_id = res["id"] if isinstance(res, dict) else res.id if hasattr(res, "id") else None
                    if new_id:
                        name_to_id[entity_record["name"]] = new_id
                        entity_record["id"] = new_id
                    entity_record["status"] = "created"
                    status_data["total_created"] += 1
                    await loop.run_in_executor(None, update_status)
                    return
                except Exception as e:
                    if attempt == 3:
                        entity_record["status"] = "failed"
                        entity_record["error"] = str(e)
                        status_data["total_failed"] += 1
                        await loop.run_in_executor(None, update_status)
                    else:
                        await asyncio.sleep(1.5 ** attempt)
                        
        for layer in layer_order:
            items = manifest.get(layer, [])
            if isinstance(items, dict): items = [items]
            for i in range(0, len(items), 5):
                batch = items[i:i+5]
                tasks = [process_entity(layer, item) for item in batch]
                await asyncio.gather(*tasks)
                
    status_data["status"] = "completed"
    await loop.run_in_executor(None, update_status)

@router.post("/hydration/{run_id}/execute")
def execute_hydration(request: Request, run_id: str, background_tasks: BackgroundTasks):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    background_tasks.add_task(run_sequential_hydration, run_id, str(context.tenant_id))
    return {"status": "started", "run_id": run_id}

@router.get("/hydration/{run_id}/status")
def get_hydration_status(request: Request, run_id: str):
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
    s3 = boto3.client("s3")
    status_key = f"{context.tenant_id}/hydration_runs/{run_id}/status.json"
    
    try:
        obj = s3.get_object(Bucket=bucket, Key=status_key)
        return json.loads(obj['Body'].read())
    except Exception as e:
        return {"status": "pending", "entities": []}
