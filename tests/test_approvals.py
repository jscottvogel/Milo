import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI, Request

from services.approvals.router import router, get_db, get_tenant_id
from services.approvals.models import Approval, Base

# Set up test app
app = FastAPI()
app.include_router(router)

# Set up test DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_create_approval(client):
    with patch("services.approvals.router.send_approval_email") as mock_email:
        res = client.post("/approvals", json={
            "title": "Test Approval",
            "requested_by": "Milo",
            "notify_email": "test@example.com",
            "options": ["approve", "reject"]
        })
        assert res.status_code == 200
        data = res.json()
        assert "approval_id" in data
        assert data["status"] == "pending"
        # Since background tasks are not executed immediately in TestClient sometimes,
        # we check the response. 

def test_read_approval(client):
    # create
    res = client.post("/approvals", json={
        "title": "Test Approval",
        "requested_by": "Milo",
        "notify_email": "test@example.com"
    })
    app_id = res.json()["approval_id"]

    # read single
    res = client.get(f"/approvals/{app_id}")
    assert res.status_code == 200
    data = res.json()["approvals"][0]
    assert data["id"] == app_id
    assert data["title"] == "Test Approval"

def test_respond_approval(client):
    res = client.post("/approvals", json={
        "title": "Test Respond",
        "requested_by": "Milo",
        "notify_email": "test@example.com"
    })
    app_id = res.json()["approval_id"]

    res = client.post(f"/approvals/{app_id}/respond", json={
        "decision": "approve",
        "decided_by": "human@example.com"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

def test_cancel_approval(client):
    res = client.post("/approvals", json={
        "title": "Test Cancel",
        "requested_by": "Milo",
        "notify_email": "test@example.com"
    })
    app_id = res.json()["approval_id"]

    res = client.request("DELETE", f"/approvals/{app_id}", json={"reason": "no longer needed"})
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

def test_expiry_logic(client):
    db = TestingSessionLocal()
    # Create an expired approval directly in DB to bypass API logic
    past_due = datetime.now(timezone.utc) - timedelta(days=1)
    approval = Approval(
        tenant_id=uuid.uuid4(),
        title="Expired",
        requested_by="Milo",
        notify_email="a@b.com",
        due_by=past_due,
        status="pending"
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    # Overriding tenant id just for this test via app override
    def override_get_tenant_id(request: Request):
        return approval.tenant_id
    app.dependency_overrides[get_tenant_id] = override_get_tenant_id
    
    res = client.get(f"/approvals")
    assert res.status_code == 200
    approvals = res.json()["approvals"]
    assert len(approvals) > 0
    assert approvals[0]["status"] == "expired"
    
    app.dependency_overrides.pop(get_tenant_id)
    db.close()

def test_inbound_email_parser(client):
    # Setup approval
    db = TestingSessionLocal()
    approval = Approval(
        tenant_id=uuid.uuid4(),
        title="Email Test",
        requested_by="Milo",
        notify_email="a@b.com",
        status="pending"
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    app_id = str(approval.id)

    payload = {
        "data": {
            "object": {
                "subject": f"Re: Action Required: Email Test {app_id}",
                "body": "APPROVE\n\nLooks good.",
                "from": [{"email": "boss@example.com"}]
            }
        }
    }

    with patch("services.approvals.email_parser.send_confirmation_email") as mock_send:
        res = client.post("/approvals/inbound-email", json=payload)
        assert res.status_code == 200
        
        db.refresh(approval)
        assert approval.status == "approved"
        assert approval.decision == "approve"
        assert approval.decided_by == "boss@example.com"
        
    db.close()
