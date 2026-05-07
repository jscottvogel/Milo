import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.middleware.auth import RequestContext
from db.models.base import Base

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.middleware("http")
async def inject_test_db(request, call_next):
    request.state.db = TestingSessionLocal()
    request.state.auth_context = RequestContext(
        tenant_id="00000000-0000-0000-0000-000000000001",
        sub="00000000-0000-0000-0000-000000000001"
    )
    # We must consume the generator or manually handle it. Actually, a simple set works because we're not testing middleware here.
    return await call_next(request)

client = TestClient(app)

def test_get_approvals_empty():
    # Pass auth header so the auth middleware succeeds
    response = client.get("/v1/approvals", headers={"Authorization": "Bearer dev_00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 200
    assert response.json() == []
