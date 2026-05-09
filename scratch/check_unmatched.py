import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.program import WorkItem

db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
engine = create_engine(db_url)
with Session(engine) as db:
    p = db.execute(select(WorkItem).where(WorkItem.name.like("Milo Platform%"))).scalar_one_or_none()
    all_items = db.execute(select(WorkItem)).scalars().all()
    
    rel = set()
    def get_all(pid):
        rel.add(pid)
        for w in all_items:
            if str(w.parent_id) == pid:
                get_all(str(w.id))
                
    get_all(str(p.id))
    items_by_id = {str(w.id): w for w in all_items}
    
    unmatched = []
    for aid in rel:
        item = items_by_id[aid]
        if item.dependencies:
            for dep in item.dependencies:
                match = False
                if dep in rel:
                    match = True
                else:
                    for x in rel:
                        if items_by_id[x].name.strip().lower() == dep.strip().lower():
                            match = True
                            break
                if not match:
                    unmatched.append((item.name, dep))
                    
    print("Unmatched:", unmatched)
