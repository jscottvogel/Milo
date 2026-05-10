import uuid
import sys
from pathlib import Path

# Add packages/db to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "packages" / "db"))

from datetime import datetime
from db.models import Base, Tenant, User, Membership, WorkItem
from db.session import db_session, SessionLocal

def seed_dev():
    print("Seeding dev database...")
    
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    
    with SessionLocal() as session:
        # Check if tenant already exists
        existing_tenant = session.query(Tenant).filter_by(id=tenant_id).first()
        if not existing_tenant:
            print("Creating tenant and user...")
            tenant = Tenant(id=tenant_id, name="Acme Corp", slug="acme", plan="team")
            user = User(id=user_id, clerk_id="user_dev123", email="dev@acme.com", full_name="Dev User")
            
            session.add(tenant)
            session.add(user)
            session.commit()
            
            membership = Membership(tenant_id=tenant_id, user_id=user_id, role="owner")
            session.add(membership)
            session.commit()

    print("Creating program data within RLS context...")
    with db_session(tenant_id) as session:
        program = WorkItem(
            tenant_id=tenant_id, 
            name="Q4 Marketing Launch",
            item_type="project",
            status="executing",
            description="Launch new product line"
        )
        session.add(program)
        session.flush() # get program.id
        
        milestone = WorkItem(
            tenant_id=tenant_id,
            parent_id=program.id,
            item_type="milestone",
            name="Design Assets Complete",
            due_date=datetime(2025, 11, 15),
            status="pending"
        )
        session.add(milestone)
        session.flush()
        
        tasks = [
            WorkItem(tenant_id=tenant_id, parent_id=milestone.id, item_type="task", name="Draft landing page copy", status="todo"),
            WorkItem(tenant_id=tenant_id, parent_id=milestone.id, item_type="task", name="Create ad creatives", status="in_progress"),
            WorkItem(tenant_id=tenant_id, parent_id=milestone.id, item_type="task", name="Review with legal", status="todo")
        ]
        session.add_all(tasks)
        session.commit()

    print("Dev database seeding complete.")

if __name__ == "__main__":
    seed_dev()
