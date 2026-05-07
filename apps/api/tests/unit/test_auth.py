import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from app.middleware.auth import AuthMiddleware
from app.config import settings

app = FastAPI()
app.add_middleware(AuthMiddleware)

@app.get("/test")
def test_route():
    return {"status": "ok"}

client = TestClient(app)

def test_missing_token():
    response = client.get("/test")
    assert response.status_code == 401
    assert "Missing token" in response.json()["error"]["message"]

def test_dev_token():
    response = client.get("/test", headers={"Authorization": "Bearer dev_tenant123"})
    assert response.status_code == 200

def test_invalid_token_format():
    response = client.get("/test", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401

def test_missing_tenant():
    response = client.get("/test", headers={"Authorization": "Bearer dev_"})
    assert response.status_code == 401

def test_invalid_jwt_structure():
    # A base64 encoded string that isn't a valid JWT
    response = client.get("/test", headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.signature"})
    assert response.status_code == 401

def test_jwks_mock():
    # Turn on COGNITO_USER_POOL_ID to hit the JWKS code path
    settings.COGNITO_USER_POOL_ID = "us-east-1_fake"
    response = client.get("/test", headers={"Authorization": "Bearer fake.token.sig"})
    assert response.status_code == 401
    settings.COGNITO_USER_POOL_ID = ""


