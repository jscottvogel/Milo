import os
from db.session import SessionLocal
from db.models.program import WorkItem
from sqlalchemy import select
import networkx as nx

db = SessionLocal()
milo_prog = db.execute(select(WorkItem).where(WorkItem.name.like("Milo Platform%"))).scalar_one_or_none()
items = db.execute(select(WorkItem)).scalars().all()
items_by_id = {str(w.id): w for w in items}

relevant_ids = set()
def collect_children(node_id):
    relevant_ids.add(node_id)
    for item in items:
        if item.parent_id and str(item.parent_id) == node_id:
            collect_children(str(item.id))

collect_children(str(milo_prog.id))

g = nx.DiGraph()
for w in items:
    if str(w.id) in relevant_ids:
        g.add_node(str(w.id))

def normalize(s):
    return s.strip().lower().replace("—", "-").replace("–", "-")

for w in items:
    if str(w.id) in relevant_ids and w.dependencies:
        for dep in w.dependencies:
            if not dep: continue
            for aid in relevant_ids:
                if normalize(items_by_id[aid].name).startswith(normalize(dep)) and aid != str(w.id):
                    print(f"Edge: {items_by_id[aid].name} -> {w.name}")
                    g.add_edge(aid, str(w.id))

topo_order = list(nx.topological_sort(g))
es = {}; ef = {}
for node in topo_order:
    duration = 1
    preds = list(g.predecessors(node))
    if not preds: es[node] = 0
    else: es[node] = max(ef[p] for p in preds)
    ef[node] = es[node] + duration
    
for n in topo_order:
    print(f"ES: {es[n]} - {items_by_id[n].name}")
