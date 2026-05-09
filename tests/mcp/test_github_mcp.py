import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi.testclient import TestClient

# We will patch the secrets manager and httpx before importing the app
# to prevent real AWS or network calls during import/startup
@pytest.fixture(autouse=True)
def mock_boto3():
    with patch("services.mcp.github.main.boto3.client") as mock_client:
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {"SecretString": '{"token": "fake-token"}'}
        mock_client.return_value = mock_secrets
        yield mock_client

@pytest.fixture
def app():
    from services.mcp.github.main import app
    return app

@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client

def test_get_token_cold_start():
    # Force reset of global cache to test cold start
    import services.mcp.github.main as main
    main._GITHUB_TOKEN = None
    token = main.get_github_token()
    assert token == "fake-token"

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_read_issues(mock_request):
    from services.mcp.github.main import read_issues, ReadIssuesInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"id": 1, "number": 100, "title": "Test Issue", "body": "...", "state": "open"}
    ]
    mock_resp.headers = {"X-RateLimit-Remaining": "5000"}
    mock_request.return_value = mock_resp

    input_data = ReadIssuesInput(repo="owner/repo", limit=1)
    res = await read_issues(input_data)
    assert "error" not in res
    assert len(res["result"]) == 1
    assert res["result"][0]["title"] == "Test Issue"

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_read_pull_requests(mock_request):
    from services.mcp.github.main import read_pull_requests, ReadPullRequestsInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"id": 1, "number": 101, "title": "Test PR", "body": "...", "state": "open"}
    ]
    mock_resp.headers = {}
    mock_request.return_value = mock_resp

    input_data = ReadPullRequestsInput(repo="owner/repo", limit=1)
    res = await read_pull_requests(input_data)
    assert len(res["result"]) == 1
    assert res["result"][0]["title"] == "Test PR"

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_read_ci_status(mock_request):
    from services.mcp.github.main import read_ci_status, ReadCiStatusInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "check_runs": [
            {"name": "test", "status": "completed", "conclusion": "success"}
        ]
    }
    mock_resp.headers = {}
    mock_request.return_value = mock_resp

    input_data = ReadCiStatusInput(repo="owner/repo", branch="main")
    res = await read_ci_status(input_data)
    assert res["result"]["status"] == "success"
    assert len(res["result"]["workflow_runs"]) == 1

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_create_issue(mock_request):
    from services.mcp.github.main import create_issue, CreateIssueInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 1, "number": 100, "html_url": "http", "title": "New", "state": "open"}
    mock_resp.headers = {"X-RateLimit-Remaining": "50"}
    mock_request.return_value = mock_resp

    input_data = CreateIssueInput(repo="owner/repo", title="New", body="Body")
    res = await create_issue(input_data)
    assert res["result"]["number"] == 100
    # verify rate limit warning
    assert res.get("rate_limit_warning") is True

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_create_branch(mock_request):
    from services.mcp.github.main import create_branch, CreateBranchInput
    # we need side_effect because it makes 2 requests
    mock_resp1 = MagicMock(spec=httpx.Response)
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = {"object": {"sha": "12345"}}
    mock_resp1.headers = {}

    mock_resp2 = MagicMock(spec=httpx.Response)
    mock_resp2.status_code = 201
    mock_resp2.json.return_value = {"object": {"sha": "12345"}, "url": "http"}
    mock_resp2.headers = {}

    mock_request.side_effect = [mock_resp1, mock_resp2]

    input_data = CreateBranchInput(repo="owner/repo", branch_name="feat", from_branch="main")
    res = await create_branch(input_data)
    assert res["result"]["branch_name"] == "feat"

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_post_comment(mock_request):
    from services.mcp.github.main import post_comment, PostCommentInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 1, "html_url": "http", "created_at": "2026-01-01T00:00:00Z"}
    mock_resp.headers = {}
    mock_request.return_value = mock_resp

    input_data = PostCommentInput(repo="owner/repo", issue_or_pr_number=1, body="Comment")
    res = await post_comment(input_data)
    assert res["result"]["comment_id"] == 1

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_read_commits(mock_request):
    from services.mcp.github.main import read_commits, ReadCommitsInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"sha": "abc", "commit": {"message": "init", "author": {"name": "Test"}}, "html_url": "http"}
    ]
    mock_resp.headers = {}
    mock_request.return_value = mock_resp

    input_data = ReadCommitsInput(repo="owner/repo")
    res = await read_commits(input_data)
    assert len(res["result"]) == 1
    assert res["result"][0]["sha"] == "abc"

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
@patch("services.mcp.github.main.get_github_token")
async def test_401_refresh(mock_get_token, mock_request):
    from services.mcp.github.main import read_issues, ReadIssuesInput
    # First response 401, second 200
    mock_resp_401 = MagicMock(spec=httpx.Response)
    mock_resp_401.status_code = 401
    mock_resp_401.json.return_value = {"message": "Bad credentials"}
    mock_resp_401.headers = {}

    mock_resp_200 = MagicMock(spec=httpx.Response)
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = []
    mock_resp_200.headers = {}

    mock_request.side_effect = [mock_resp_401, mock_resp_200]
    mock_get_token.return_value = "new-token"

    input_data = ReadIssuesInput(repo="owner/repo")
    res = await read_issues(input_data)
    assert "error" not in res
    assert mock_request.call_count == 2
    mock_get_token.assert_called()

@pytest.mark.asyncio
@patch("services.mcp.github.main.http_client.request", new_callable=AsyncMock)
async def test_api_error_structured_return(mock_request):
    from services.mcp.github.main import read_issues, ReadIssuesInput
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"message": "Not Found"}
    mock_resp.headers = {}
    mock_request.return_value = mock_resp

    input_data = ReadIssuesInput(repo="owner/repo")
    res = await read_issues(input_data)
    assert res["error"] == "Not Found"
    assert res["github_status"] == 404
