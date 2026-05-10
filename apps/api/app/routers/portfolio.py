import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Query
from sqlalchemy import select, and_, or_, func

from db.models.program import WorkItem, Risk

router = APIRouter(prefix="/v1/portfolio", tags=["Portfolio"])

@router.get("")
def get_portfolio(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by program status (active, planned, complete)"),
    owner_name: Optional[str] = Query(None, description="Filter by owner name")
):
    """
    Get a portfolio view of all active programs (objectives, initiatives, projects)
    with aggregated health metrics.
    """
    context = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
        
    tenant_id = context.tenant_id

    # 1. Base query for programs
    stmt = select(WorkItem).where(
        WorkItem.tenant_id == tenant_id,
        WorkItem.item_type.in_(["objective", "initiative", "project"])
    )
    
    if status:
        stmt = stmt.where(WorkItem.status == status)
    if owner_name:
        stmt = stmt.where(WorkItem.owner_name == owner_name)
        
    programs = db.scalars(stmt).all()
    
    # 2. Get all child items and risks for the tenant to do memory aggregation
    # Alternatively we can query per program, but fetching all is simpler for small-to-medium tenants
    # For robust performance, we'll do targeted queries per program, or CTEs.
    # Let's do it per program for simplicity.
    
    results = []
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    
    for prog in programs:
        # A. Milestones
        milestone_count = db.scalar(
            select(func.count(WorkItem.id)).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.parent_id == prog.id,
                WorkItem.item_type == "milestone"
            )
        ) or 0
        
        # B. Overdue Tasks
        # Tasks are children of the program (direct or indirect). For PoC, assume direct or via 1 level.
        # To be safe, we can just check tasks where parent_id = prog.id.
        # If Milo creates a hierarchy, we might need a recursive CTE. 
        # But let's assume tasks are tied to the program directly or through a milestone.
        # Let's do direct tasks and tasks under milestones of this program.
        sub_stmt = select(WorkItem.id).where(WorkItem.parent_id == prog.id)
        
        overdue_task_count = db.scalar(
            select(func.count(WorkItem.id)).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.item_type == "task",
                WorkItem.status != "completed",
                WorkItem.due_date < now,
                or_(
                    WorkItem.parent_id == prog.id,
                    WorkItem.parent_id.in_(sub_stmt)
                )
            )
        ) or 0
        
        # Stalled milestones
        stalled_milestone_count = db.scalar(
            select(func.count(WorkItem.id)).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.parent_id == prog.id,
                WorkItem.item_type == "milestone",
                WorkItem.status != "completed",
                WorkItem.due_date < now
            )
        ) or 0

        # C. Risks
        open_risks = db.scalars(
            select(Risk).where(
                Risk.tenant_id == tenant_id,
                Risk.work_item_id == prog.id,
                Risk.status == "open"
            )
        ).all()
        
        open_risk_count = len(open_risks)
        has_critical_risk = any(r.impact == 5 and r.likelihood >= 4 for r in open_risks)
        
        # D. Budget Variance
        meta = prog.metadata_json or {}
        budget_variance_pct = meta.get("budget_variance_pct", 0)
        
        # Calculate RAG Health
        # RED = any overdue milestone or critical unresolved risk
        # YELLOW = overdue tasks or budget variance > 10%
        # GREEN = all clear
        health_rag = "green"
        if stalled_milestone_count > 0 or has_critical_risk:
            health_rag = "red"
        elif overdue_task_count > 0 or budget_variance_pct > 10:
            health_rag = "amber" # Using 'amber' for UI compatibility
            
        results.append({
            "program_id": str(prog.id),
            "name": prog.name,
            "status": prog.status,
            "health": health_rag,
            "milestone_count": milestone_count,
            "overdue_task_count": overdue_task_count,
            "open_risk_count": open_risk_count,
            "budget_variance_pct": budget_variance_pct,
            "metadata": meta,
            "due_date": prog.due_date.isoformat() if prog.due_date else None,
            "owner_name": prog.owner_name
        })
        
    # 3. Compute Resource Heatmap
    # Group tasks by owner_name and program
    # Tasks could be tied to a milestone (parent = milestone, grand_parent = program) or directly to program.
    # For simplicity, we just count tasks where owner_name is not null.
    from sqlalchemy import func
    
    heatmap_stmt = select(
        WorkItem.owner_name,
        func.count(WorkItem.id).label("task_count")
    ).where(
        WorkItem.tenant_id == tenant_id,
        WorkItem.item_type == "task",
        WorkItem.status != "completed",
        WorkItem.owner_name != None
    ).group_by(WorkItem.owner_name)
    
    heatmap_rows = db.execute(heatmap_stmt).all()
    resource_heatmap = [{"owner_name": row[0], "task_count": row[1]} for row in heatmap_rows]

    return {
        "portfolio": results,
        "resource_heatmap": resource_heatmap
    }
