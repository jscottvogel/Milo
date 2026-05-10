import uuid

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_ok():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"api": "ok", "database": "ok"}


def test_health_db_error(mocker):
    mocker.patch(
        "apps.api.app.routers.health.create_engine",
        side_effect=Exception("DB connection failed"),
    )
    response = client.get("/v1/health")
    assert response.status_code == 503
    assert response.json() == {"api": "ok", "database": "error"}

def test_get_me_unauthorized():
    response = client.get("/v1/me")
    assert response.status_code == 401

def test_create_tenant():
    valid_uuid = str(uuid.uuid4())
    slug = f"test-tenant-{valid_uuid[:8]}"
    response = client.post(
        "/v1/tenants",
        json={"name": "Test Tenant", "slug": slug},
        headers={"Authorization": f"Bearer dev_{valid_uuid}"}
    )
    print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Tenant"

def test_get_me():
    valid_uuid = str(uuid.uuid4())
    response = client.get("/v1/me", headers={"Authorization": f"Bearer dev_{valid_uuid}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Dev User"

def test_get_tenant_forbidden():
    valid_uuid = str(uuid.uuid4())
    other_tenant_id = str(uuid.uuid4())
    response = client.get(f"/v1/tenants/{other_tenant_id}", headers={"Authorization": f"Bearer dev_{valid_uuid}"})
    assert response.status_code == 403

def test_stubs():
    valid_uuid = str(uuid.uuid4())
    response = client.get("/v1/integrations", headers={"Authorization": f"Bearer dev_{valid_uuid}"})
    assert response.status_code == 501

def test_validation_error():
    valid_uuid = str(uuid.uuid4())
    # Missing required 'slug' field
    response = client.post(
        "/v1/tenants",
        json={"name": "Test Tenant"},
        headers={"Authorization": f"Bearer dev_{valid_uuid}"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

def test_not_found_error():
    response = client.get("/v1/doesnotexist")
    assert response.status_code == 404
