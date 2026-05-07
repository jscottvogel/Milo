import uuid
import sys
from pathlib import Path

# Add packages/db to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "packages" / "db"))

from datetime import datetime
from db.models import Base, Tenant, User, Membership, Program, Milestone, Task
from db.session import db_session, SessionLocal

def seed_dev():
    print("Seeding dev database...")
    
    tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    user_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    
    # We must first create the tenant before we can use the RLS-enabled session,
    # or we can use a raw session to bypass RLS for the tenant creation.
    # Actually, RLS usually requires app.tenant_id to be set to the tenant_id.
    
    with SessionLocal() as session:
        # Check if tenant already exists
        existing_tenant = session.query(Tenant).filter_by(id=tenant_id).first()
        if existing_tenant:
            print("Database already seeded.")
            return

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
        program = Program(
            tenant_id=tenant_id, 
            name="Q4 Marketing Launch",
            status="executing",
            charter={"goal": "Launch new product line"}
        )
        session.add(program)
        session.flush() # get program.id
        
        milestone = Milestone(
            tenant_id=tenant_id,
            program_id=program.id,
            name="Design Assets Complete",
            target_date=datetime(2025, 11, 15),
            status="pending"
        )
        session.add(milestone)
        session.flush()
        
        tasks = [
            Task(tenant_id=tenant_id, program_id=program.id, milestone_id=milestone.id, title="Draft landing page copy", status="todo"),
            Task(tenant_id=tenant_id, program_id=program.id, milestone_id=milestone.id, title="Create ad creatives", status="in_progress"),
            Task(tenant_id=tenant_id, program_id=program.id, milestone_id=milestone.id, title="Review with legal", status="todo")
        ]
        session.add_all(tasks)
        session.commit()

    print("Dev database seeding complete.")

if __name__ == "__main__":
    seed_dev()
