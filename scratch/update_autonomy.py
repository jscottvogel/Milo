import os
from dotenv import load_dotenv
import uuid

os.environ["DATABASE_URL"] = "postgresql+psycopg://milo_user:milo_password@localhost:5432/milo"
load_dotenv()

from db.session import SessionLocal
from db.models.identity import Milo

def update():
    tenant_id = "00000000-0000-0000-0000-000000000001"
    with SessionLocal() as session:
        milo = session.query(Milo).filter(Milo.tenant_id == uuid.UUID(tenant_id)).first()
        if not milo:
            print("Milo not found for tenant")
            return
            
        levels = milo.autonomy_levels.copy() if milo.autonomy_levels else {}
        levels["email.send"] = "auto"
        milo.autonomy_levels = levels
        
        session.commit()
        print(f"Updated autonomy levels for {tenant_id}: {milo.autonomy_levels}")

if __name__ == "__main__":
    update()
