import os
from db.session import SessionLocal
from db.models.program import WorkItem
from sqlalchemy import select
import networkx as nx

db = SessionLocal()
items = db.execute(select(WorkItem)).scalars().all()
items_by_id = {str(w.id): w for w in items}

g = nx.DiGraph()
for w in items:
    g.add_node(str(w.id))

def normalize(s):
    return s.strip().lower().replace("—", "-").replace("–", "-")

for w in items:
    if w.dependencies:
        for dep in w.dependencies:
            if not dep: continue
            for aid in items_by_id:
                if normalize(items_by_id[aid].name).startswith(normalize(dep)) and aid != str(w.id):
                    print(f"Edge: {items_by_id[aid].name} -> {w.name}")
                    g.add_edge(aid, str(w.id))

print(f"Num edges: {g.number_of_edges()}")
for n in g.nodes():
    print(f"Node: {items_by_id[n].name}, In-Degree: {g.in_degree(n)}")
