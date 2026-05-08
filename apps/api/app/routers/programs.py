import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models.program import WorkItem, Risk, Decision, ChangeRequest, Stakeholder, Commitment

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


def build_tree(items: list[WorkItem], parent_id: uuid.UUID | None, all_risks: list[Risk] | None = None, all_crs: list[ChangeRequest] | None = None, all_decisions: list[Decision] | None = None, all_stakeholders: list[Stakeholder] | None = None, all_action_items: list[Commitment] | None = None) -> list[WorkItemTreeResponse]:
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
                    id=str(sh.id), work_item_id=str(sh.work_item_id) if sh.work_item_id else None,
                    name=sh.name, email=sh.email, role=sh.role, influence=sh.influence, interest=sh.interest, satisfaction=sh.satisfaction, notes=sh.notes
                ) for sh in all_stakeholders if sh.work_item_id == item.id
            ]
            node_action_items = [
                ActionItemResponse(
                    id=str(ci.id), work_item_id=str(ci.work_item_id) if ci.work_item_id else None,
                    description=ci.description, owner_name=ci.owner_name, due_date=ci.due_date.isoformat() if ci.due_date else None, status=ci.status
                ) for ci in all_action_items if ci.work_item_id == item.id
            ]
            node = WorkItemTreeResponse(
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
                children=build_tree(items, item.id, all_risks, all_crs, all_decisions, all_stakeholders, all_action_items),
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
    all_stakeholders = db.scalars(select(Stakeholder).where(Stakeholder.tenant_id == tenant_id)).all()
    all_action_items = db.scalars(select(Commitment).where(Commitment.tenant_id == tenant_id)).all()
    
    return build_tree(all_items, None, all_risks, all_crs, all_decisions, all_stakeholders, all_action_items)

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
    all_stakeholders = db.scalars(select(Stakeholder).where(Stakeholder.tenant_id == uuid.UUID(tenant_id))).all()
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
            id=str(sh.id), work_item_id=str(sh.work_item_id) if sh.work_item_id else None,
            name=sh.name, email=sh.email, role=sh.role, influence=sh.influence, interest=sh.interest, satisfaction=sh.satisfaction, notes=sh.notes
        ) for sh in all_stakeholders if sh.work_item_id == item.id
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
    # Ensure safe filename
    safe_filename = "".join(c for c in payload.filename if c.isalnum() or c in "._- ")
    key = f"{tenant_id}/work_items/{item_id}/{int(time.time())}_{safe_filename}"
    
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': bucket,
            'Key': key,
            'ContentType': payload.content_type
        },
        ExpiresIn=3600
    )
    
    return PresignedUrlResponse(upload_url=url, key=key)
