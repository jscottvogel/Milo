import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Helper to mock auth context
def override_auth_context(tenant_id: str):
    async def mock_auth(request):
        class MockContext:
            def __init__(self, tenant_id):
                self.tenant_id = tenant_id
        request.state.auth_context = MockContext(tenant_id)
    return mock_auth

@pytest.fixture(autouse=True)
def setup_auth(monkeypatch):
    # We bypass the actual JWT verification for tests
    monkeypatch.setattr("app.middleware.auth.AuthMiddleware.dispatch", 
        lambda self, request, call_next: call_next(request))

def test_github_read_issues_unconfigured(monkeypatch):
    # Mock tenant id explicitly
    monkeypatch.setattr("app.routers.github.get_tenant_id_from_request", lambda r: "tenant-123")
    # Mock token to None
    monkeypatch.setattr("app.routers.github.get_github_token", lambda t, force=False: None)
    
    response = client.post("/v1/github/read_issues", json={
        "repo": "owner/repo",
        "limit": 5
    })
    
    # Fast api validation will pass, our handler returns 200 with an error field
    assert response.status_code == 200
    data = response.json()
    assert "GitHub integration is not configured" in data["error"]

def test_slack_send_message_unconfigured(monkeypatch):
    monkeypatch.setattr("app.routers.slack.get_tenant_id_from_request", lambda r: "tenant-123")
    monkeypatch.setattr("app.routers.slack.get_slack_token", lambda t: None)
    
    response = client.post("/v1/slack/send_message", json={
        "channel": "#general",
        "text": "Hello world"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Slack integration is not configured" in data["error"]

def test_jira_search_issues_unconfigured(monkeypatch):
    monkeypatch.setattr("app.routers.jira.get_tenant_id_from_request", lambda r: "tenant-123")
    monkeypatch.setattr("app.routers.jira.get_jira_credentials", lambda t: None)
    
    response = client.post("/v1/jira/search_issues", json={
        "jql": "project = MILO",
        "max_results": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Jira integration is not configured" in data["error"]
