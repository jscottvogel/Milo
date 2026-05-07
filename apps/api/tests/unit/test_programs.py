from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_get_programs_unauthorized():
    # Without auth header, auth middleware will reject if we test it properly, 
    # but the middleware only adds auth_context if token exists. If no token, 
    # the endpoint's `if not context: raise 401` kicks in.
    response = client.get("/v1/programs")
    assert response.status_code == 401

def test_create_program_validation():
    response = client.post("/v1/programs", json={}, headers={"Authorization": "Bearer dev_00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 422
