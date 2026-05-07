import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.routers.approvals import get_current_tenant_id, get_current_user_id
from db.session import get_db
from db.models.base import Base

# Setup in-memory sqlite db for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_tenant_id():
    return "00000000-0000-0000-0000-000000000001"

def override_get_user_id():
    return "00000000-0000-0000-0000-000000000001"

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_tenant_id] = override_get_tenant_id
app.dependency_overrides[get_current_user_id] = override_get_user_id

client = TestClient(app)

def test_get_approvals_empty():
    response = client.get("/v1/approvals")
    assert response.status_code == 200
    assert response.json() == []
