import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.program import WorkItem
import networkx as nx

def check_dependencies():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    engine = create_engine(db_url)
    with Session(engine) as db:
        milo_prog = db.execute(select(WorkItem).where(WorkItem.name.like("Milo Platform%"))).scalar_one_or_none()
        all_items = db.execute(select(WorkItem)).scalars().all()
        
        relevant_ids = set()
        def collect_children(node_id):
            relevant_ids.add(node_id)
            for item in all_items:
                if item.parent_id and str(item.parent_id) == node_id:
                    collect_children(str(item.id))
                    
        collect_children(str(milo_prog.id))
        items_by_id = {str(item.id): item for item in all_items}
        
        graph = nx.DiGraph()
        for item_id in relevant_ids:
            duration = 1
            item = items_by_id[item_id]
            if item.start_date and item.due_date:
                duration = max(1, (item.due_date - item.start_date).days)
            graph.add_node(item_id, name=item.name, duration=duration)
            
        for item_id in relevant_ids:
            item = items_by_id[item_id]
            if item.dependencies:
                for dep in item.dependencies:
                    dep_id = None
                    if dep in items_by_id:
                        dep_id = dep
                    else:
                        def normalize(s):
                            return s.strip().lower().replace("—", "-").replace("–", "-")
                        for aid in relevant_ids:
                            if normalize(items_by_id[aid].name).startswith(normalize(dep)):
                                dep_id = aid
                                break
                    if dep_id and dep_id in relevant_ids:
                        graph.add_edge(dep_id, item_id)
                        
        topo_order = list(nx.topological_sort(graph))
        es = {}; ef = {}
        for node in topo_order:
            duration = graph.nodes[node].get("duration", 1)
            preds = list(graph.predecessors(node))
            if not preds: es[node] = 0
            else: es[node] = max(ef[p] for p in preds)
            ef[node] = es[node] + duration
            
        ls = {}; lf = {}
        # Calculate project_duration based explicitly on the program's due_date if available
        program_item = items_by_id.get(str(milo_prog.id))
        if program_item and program_item.start_date and program_item.due_date:
            project_duration = max(1, (program_item.due_date - program_item.start_date).days)
        else:
            connected_nodes = [n for n in topo_order if list(graph.predecessors(n)) or list(graph.successors(n))]
            project_duration = max([ef[n] for n in connected_nodes]) if connected_nodes else (max(ef.values()) if ef else 0)
        
        for node in reversed(topo_order):
            duration = graph.nodes[node].get("duration", 1)
            succs = list(graph.successors(node))
            if not succs: lf[node] = project_duration
            else: lf[node] = min(ls[s] for s in succs)
            ls[node] = lf[node] - duration
            
        for node in topo_order:
            float_val = ls[node] - es[node]
            item_type = items_by_id[node].item_type if node in items_by_id else "unknown"
            
            # Validation assertion for negative float
            if float_val < 0 and program_item and program_item.due_date and items_by_id[node].due_date:
                if items_by_id[node].due_date <= program_item.due_date:
                    raise ValueError(f"Negative float {float_val} on {items_by_id[node].name} but due date is within program window")
                    
            if float_val <= 0 and item_type in ("milestone", "phase-gate"):
                print(f"CRITICAL: {graph.nodes[node]['name']} (Type: {item_type}, Float: {float_val})")
            elif "Phase" in graph.nodes[node]['name']:
                print(f"NON-CRITICAL Phase: {graph.nodes[node]['name']} (Float: {float_val})")

if __name__ == "__main__":
    check_dependencies()
