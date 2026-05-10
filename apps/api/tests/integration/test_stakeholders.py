import pytest
import uuid
import datetime
from fastapi.testclient import TestClient

from app.main import app
from db.session import SessionLocal
from db.models.program import WorkItem, ProgramStakeholder
from db.models.identity import Tenant, Milo

client = TestClient(app)

@pytest.fixture
def test_data():
    tenant_id = uuid.uuid4()
    program_id = uuid.uuid4()
    sh1_sub = uuid.uuid4()
    sh2_sub = uuid.uuid4()
    
    with SessionLocal() as db:
        tenant = Tenant(id=tenant_id, name="Test Tenant", slug=f"test-tenant-{tenant_id}")
        db.add(tenant)
        db.commit()
        
        milo = Milo(id=uuid.uuid4(), tenant_id=tenant_id, name="Test Milo", persona_pack="sme")
        db.add(milo)
        
        program = WorkItem(
            id=program_id,
            tenant_id=tenant_id,
            name="Test Program",
            item_type="project"
        )
        db.add(program)
        db.commit()
        
        sh1 = ProgramStakeholder(
            stakeholder_sub=sh1_sub,
            tenant_id=tenant_id,
            program_id=program_id,
            email="sponsor@example.com",
            role="sponsor",
            influence="high",
            interest="high",
            status="active"
        )
        
        sh2 = ProgramStakeholder(
            stakeholder_sub=sh2_sub,
            tenant_id=tenant_id,
            program_id=program_id,
            email="observer@example.com",
            role="observer",
            influence="low",
            interest="low",
            status="pending"
        )
        
        db.add_all([sh1, sh2])
        db.commit()
        
    yield {"tenant_id": str(tenant_id), "program_id": str(program_id), "sh1_sub": str(sh1_sub), "sh2_sub": str(sh2_sub)}
    
    with SessionLocal() as db:
        db.query(Tenant).filter(Tenant.id == tenant_id).delete()
        db.commit()


def test_get_stakeholders(test_data):
    tenant_id = test_data["tenant_id"]
    
    headers = {"Authorization": f"Bearer dev_{tenant_id}"}
    response = client.get(f"/v1/stakeholders?program_id={test_data['program_id']}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(d["email"] == "sponsor@example.com" for d in data)

def test_search_stakeholders(test_data):
    tenant_id = test_data["tenant_id"]
    
    headers = {"Authorization": f"Bearer dev_{tenant_id}"}
    
    # Search by free-text
    response = client.get("/v1/stakeholders/search?query=sponsor", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "sponsor@example.com"
    
    # Filter by influence
    response = client.get("/v1/stakeholders/search?influence=low", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "observer@example.com"
