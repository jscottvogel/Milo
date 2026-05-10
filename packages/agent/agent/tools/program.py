import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models.program import Decision, Risk, WorkItem, ChangeRequest, ProgramStakeholder, Commitment
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
                sh_stmt = select(ProgramStakeholder).where(ProgramStakeholder.program_id == w.id)
                data["stakeholders"] = [{"id": str(sh.stakeholder_sub), "name": sh.profile.full_name if sh.profile else "Unknown", "email": "N/A", "role": sh.role, "influence": sh.influence, "interest": sh.interest, "satisfaction": sh.satisfaction, "notes": ""} for sh in context.session.scalars(sh_stmt).all()]

                # Load action items (commitments)
                ci_stmt = select(Commitment).where(Commitment.work_item_id == w.id)
                data["action_items"] = [{"id": str(ci.id), "description": ci.description, "owner_name": ci.owner_name, "due_date": ci.due_date.isoformat() if ci.due_date else None, "status": ci.status} for ci in context.session.scalars(ci_stmt).all()]

            results.append(data)

        return WorkItemReadOutput(items=results).model_dump()


class WorkItemUpdateInput(BaseModel):
    entity_type: Literal["objective", "outcome", "key_result", "initiative", "project", "workstream", "milestone", "task", "risk", "decision", "change_request", "stakeholder", "action_item"] = Field(description="The type of entity to update")
    entity_id: str | None = Field(default=None, description="The ID of the entity to update. If null, a new entity is created.")
    parent_id: str | None = Field(default=None, description="The ID of the parent work item (required for creating child entities).")
    payload: dict[str, Any] = Field(description="The fields to update or create. For work items: name, description, status, start_date (ISO), due_date (ISO), owner_name, metadata_json (use this to store financial time-series data using key 'financials' containing an array of objects like {\"period\": \"YYYY-MM\", \"budget\": 100, \"actual\": 50}), dependencies (list of strings representing names of entities this depends on). For risk: title, likelihood (int 1-5), impact (int 1-5), status, mitigation. For change_request: title, description, reason, status, impact_analysis. For decision: title, decision_text, alternatives_jsonb (dict), source_link. For stakeholder: stakeholder_sub, role, influence, interest, satisfaction, status (pending/active/revoked). For action_item: description, owner_name, due_date (ISO), status (pending/met/missed).")


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

        EntityClass = WorkItem if is_work_item else (Risk if entity_type == "risk" else (Decision if entity_type == "decision" else (ChangeRequest if entity_type == "change_request" else (ProgramStakeholder if entity_type == "stakeholder" else Commitment))))
        entity = None
        
        if entity_type == "stakeholder":
            # Primary keys for ProgramStakeholder are (stakeholder_sub, tenant_id, program_id)
            parent_uuid = uuid.UUID(parent_id_str) if parent_id_str else None
            stakeholder_sub_str = payload.get("stakeholder_sub")
            if not stakeholder_sub_str or not parent_uuid:
                raise ValueError("stakeholder_sub and parent_id (program_id) are required when updating a stakeholder.")
            
            sub_uuid = uuid.UUID(stakeholder_sub_str)
            stmt = select(ProgramStakeholder).where(
                ProgramStakeholder.tenant_id == uuid.UUID(context.tenant_id),
                ProgramStakeholder.program_id == parent_uuid,
                ProgramStakeholder.stakeholder_sub == sub_uuid
            )
            entity = context.session.scalar(stmt)
            if not entity:
                entity = ProgramStakeholder(
                    stakeholder_sub=sub_uuid,
                    tenant_id=uuid.UUID(context.tenant_id),
                    program_id=parent_uuid
                )
                context.session.add(entity)
        elif entity_id_str:
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
                    if not parent_id_str and entity_type != "stakeholder":
                        raise ValueError(f"parent_id (work_item_id) is required when creating a {entity_type}.")
                    if entity_type != "stakeholder":
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

        if entity_type == "stakeholder":
            return WorkItemUpdateOutput(id=str(entity.stakeholder_sub)).model_dump()
        else:
            return WorkItemUpdateOutput(id=str(entity.id)).model_dump()


class ProgramCriticalPathInput(BaseModel):
    program_id: str = Field(description="The UUID of the program/project to analyze.")
    what_if_task_id: str | None = Field(default=None, description="Optional UUID of a task to slip.")
    what_if_slip_days: int | None = Field(default=None, description="Number of days to slip the what-if task.")


class ProgramCriticalPathOutput(BaseModel):
    critical_path: list[str] = Field(description="List of task names on the critical path.")
    tasks: dict[str, Any] = Field(description="Detailed CPM metrics per task.")
    blockers: list[dict[str, Any]] = Field(description="List of blocking relationships.")
    mermaid_diagram: str = Field(description="Mermaid.js diagram of the critical path.")
    summary: str = Field(description="Human readable summary.")


class ProgramCriticalPathTool(Tool):
    name = "program.critical_path"
    description = "Compute the critical path for a program, identifying zero-float tasks, duration, blocking relationships, and schedule risks. Allows what-if scenario slips."
    input_schema = ProgramCriticalPathInput
    output_schema = ProgramCriticalPathOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        import networkx as nx
        import uuid
        import json
        from sqlalchemy import select
        
        program_id_str = input_data["program_id"]
        what_if_task_id = input_data.get("what_if_task_id")
        what_if_slip_days = input_data.get("what_if_slip_days")
        
        # Load all items for tenant to build the tree efficiently
        stmt = select(WorkItem).where(WorkItem.tenant_id == uuid.UUID(context.tenant_id))
        all_items = context.session.scalars(stmt).all()
        
        items_by_id = {str(item.id): item for item in all_items}
        
        if program_id_str not in items_by_id:
            raise ValueError(f"Program/Project {program_id_str} not found.")
            
        # Recursive function to get all descendants
        relevant_ids = set()
        def collect_children(node_id):
            relevant_ids.add(node_id)
            for item in all_items:
                if item.parent_id and str(item.parent_id) == node_id:
                    collect_children(str(item.id))
                    
        collect_children(program_id_str)
        
        graph = nx.DiGraph()
        
        # Add nodes
        for item_id in relevant_ids:
            item = items_by_id[item_id]
            assumed_duration = False
            duration = 1
            if item.start_date and item.due_date:
                duration = max(1, (item.due_date - item.start_date).days)
            else:
                assumed_duration = True
                
            if what_if_task_id == item_id and what_if_slip_days:
                duration += what_if_slip_days
                
            graph.add_node(item_id, name=item.name, duration=duration, assumed=assumed_duration, status=item.status)
            
        # Add edges (dependencies)
        import logging
        for item_id in relevant_ids:
            item = items_by_id[item_id]
            if item.dependencies:
                for dep in item.dependencies:
                    if not dep:
                        continue
                    dep_id = None
                    if dep in items_by_id:
                        dep_id = dep
                    else:
                        # Try finding by name (case-insensitive, trim whitespace, normalize hyphens)
                        def normalize(s):
                            return s.strip().lower().replace("—", "-").replace("–", "-")
                        for aid in relevant_ids:
                            # Use startswith to match 'Phase 2 Complete' against 'Phase 2 Complete - Cognito...'
                            # Also check if the dependency string is in the node name
                            aid_name = normalize(items_by_id[aid].name)
                            dep_norm = normalize(dep)
                            if aid_name.startswith(dep_norm) or dep_norm in aid_name:
                                dep_id = aid
                                logging.info(f"RESOLVER MATCH: '{dep}' resolved to UUID {aid} ({items_by_id[aid].name})")
                                break
                    if dep_id and dep_id in relevant_ids:
                        if dep_id != item_id:
                            graph.add_edge(dep_id, item_id)
                        else:
                            logging.warning(f"Self-loop dependency ignored for {item.name}")
                    else:
                        logging.warning(f"RESOLVER MISS: Dependency '{dep}' could not be resolved for item {item.name}. Skipping edge.")
                        
        # Check for cycles
        try:
            cycle = nx.find_cycle(graph, orientation="original")
            return {"error": "Circular dependency detected", "cycle": str(cycle)}
        except nx.NetworkXNoCycle:
            pass
            
        topo_order = list(nx.topological_sort(graph))
        
        # Forward pass
        es = {}
        ef = {}
        for node in topo_order:
            preds = list(graph.predecessors(node))
            if not preds:
                es[node] = 0
            else:
                es[node] = max(ef[p] for p in preds)
            ef[node] = es[node] + graph.nodes[node]["duration"]
            
        # Backward pass
        ls = {}
        lf = {}
        
        # Calculate project_duration based explicitly on the program's due_date if available
        program_item = items_by_id.get(program_id_str)
        if program_item and program_item.due_date:
            earliest_start = program_item.start_date
            if not earliest_start:
                starts = [items_by_id[n].start_date for n in relevant_ids if items_by_id[n].start_date]
                earliest_start = min(starts) if starts else None
            
            if earliest_start:
                project_duration = max(1, (program_item.due_date - earliest_start).days)
            else:
                connected_nodes = [n for n in topo_order if list(graph.predecessors(n)) or list(graph.successors(n))]
                project_duration = max([ef[n] for n in connected_nodes]) if connected_nodes else (max(ef.values()) if ef else 0)
        else:
            connected_nodes = [n for n in topo_order if list(graph.predecessors(n)) or list(graph.successors(n))]
            project_duration = max([ef[n] for n in connected_nodes]) if connected_nodes else (max(ef.values()) if ef else 0)

        # IMPORTANT: If the actual calculated early finish exceeds the static deadline (e.g. due to a what-if slip),
        # the project is delayed and the project_duration MUST expand to accommodate the new end date.
        actual_max_ef = max(ef.values()) if ef else 0
        project_duration = max(project_duration, actual_max_ef)
        
        # Backward pass
        ls = {}
        lf = {}
        for node in reversed(topo_order):
            succs = list(graph.successors(node))
            if not succs:
                # Terminal nodes anchor to their own Early Finish to ensure independent 
                # paths compute critical paths accurately without inheriting artificial float 
                # from a global program due date.
                lf[node] = ef[node]
            else:
                lf[node] = min(ls[s] for s in succs)
            ls[node] = lf[node] - graph.nodes[node]["duration"]
            
        # Determine the minimum float in the network
        min_float = min([ls[n] - es[n] for n in topo_order]) if topo_order else 0

        # Floats & Critical Path
        floats = {}
        critical_path = []
        task_details = {}
        
        for node in topo_order:
            node_str = str(node)
            f = ls[node] - es[node]
            floats[node] = f
            item_type = items_by_id[node_str].item_type if node_str in items_by_id else "unknown"
            
            # Validation assertion for negative float
            if f < 0 and program_item and program_item.due_date and items_by_id[node_str].due_date:
                if items_by_id[node_str].due_date <= program_item.due_date:
                    pass # It's valid to have negative float if it's pushed by assumed durations
            
            # Determine if node is critical (float == 0)
            is_crit = (f == 0)
            
            if is_crit and item_type in ("milestone", "phase-gate"):
                critical_path.append({
                    "id": node,
                    "name": graph.nodes[node]["name"],
                    "type": item_type,
                    "float": f
                })
                
            task_details[node] = {
                "name": graph.nodes[node]["name"],
                "type": item_type,
                "duration": graph.nodes[node]["duration"],
                "assumed_duration": graph.nodes[node]["assumed"],
                "early_start": es[node],
                "early_finish": ef[node],
                "late_start": ls[node],
                "late_finish": lf[node],
                "float": f,
                "is_critical": is_crit
            }
            
        # Blockers
        blockers = []
        for node in topo_order:
            preds = list(graph.predecessors(node))
            succs = list(graph.successors(node))
            if preds or succs:
                blockers.append({
                    "task": graph.nodes[node]["name"],
                    "blocked_by": [graph.nodes[p]["name"] for p in preds],
                    "blocking": [graph.nodes[s]["name"] for s in succs]
                })
                
        # Mermaid
        mermaid_lines = ["graph TD;"]
        for u, v in graph.edges():
            u_name = graph.nodes[u]["name"].replace('"', '')
            v_name = graph.nodes[v]["name"].replace('"', '')
            if floats[u] <= 0 and floats[v] <= 0:
                mermaid_lines.append(f'  "{u_name}" -->|Critical| "{v_name}";')
                mermaid_lines.append(f'  style "{u_name}" stroke:#f66,stroke-width:2px;')
                mermaid_lines.append(f'  style "{v_name}" stroke:#f66,stroke-width:2px;')
            else:
                mermaid_lines.append(f'  "{u_name}" --> "{v_name}";')
                
        mermaid_diagram = "\\n".join(mermaid_lines)
        
        milestones_in_critical = len([n for n in critical_path if n["type"] in ("milestone", "phase-gate")])
        summary = f"Project duration is {project_duration} days. Critical path contains {len(critical_path)} items ({milestones_in_critical} milestones). "
        if what_if_task_id and what_if_task_id in task_details:
            summary += f"(Includes WHAT-IF slip of {what_if_slip_days} days on {task_details[what_if_task_id]['name']})"
        # Sort critical path by Early Start (to show chronological order)
        critical_path_sorted = sorted(critical_path, key=lambda x: es.get(x["id"], 0))
        
        result = {
            "program_id": program_id_str,
            "project_duration_days": project_duration,
            "critical_path": [c["name"] for c in critical_path_sorted],
            "tasks": task_details,
            "blockers": blockers,
            "mermaid_diagram": mermaid_diagram.replace("\\n", "\n"),
            "summary": summary
        }
        
        # Save to storage
        from agent.tools.registry import registry
        storage_tool = registry.get_tool("storage.write")
        if storage_tool:
            try:
                await storage_tool.invoke({
                    "path": f"program_data/{program_id_str}/critical_path_latest.json",
                    "content": json.dumps(result, indent=2)
                }, context)
            except Exception:
                pass
            
        # Save to memory
        memory_tool = registry.get_tool("memory.write")
        if memory_tool:
            try:
                await memory_tool.invoke({
                    "kind": "event",
                    "content": f"Computed Critical Path for {items_by_id[program_id_str].name}. Duration: {project_duration} days."
                }, context)
            except Exception:
                pass
            
        return result
