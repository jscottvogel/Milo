from contextlib import asynccontextmanager
import os
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import httpx
import boto3

# Global cache for the GitHub token
_GITHUB_TOKEN = None
_SECRET_NAME = "milo/github/token"
_REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")

def get_github_token(force_refresh: bool = False) -> str:
    global _GITHUB_TOKEN
    if not _GITHUB_TOKEN or force_refresh:
        try:
            client = boto3.client('secretsmanager', region_name=_REGION_NAME)
            response = client.get_secret_value(SecretId=_SECRET_NAME)
            # Assuming the secret is just the token string or JSON with a 'token' key
            secret_string = response.get('SecretString', '')
            import json
            try:
                secret_dict = json.loads(secret_string)
                _GITHUB_TOKEN = secret_dict.get('token', secret_string)
            except json.JSONDecodeError:
                _GITHUB_TOKEN = secret_string
        except Exception as e:
            # Fallback to env var for local testing if secrets manager fails
            _GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
            if not _GITHUB_TOKEN:
                raise RuntimeError(f"Failed to fetch GitHub token: {e}")
    return _GITHUB_TOKEN

# Initialize httpx client
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # Cold start token fetch
    try:
        get_github_token()
    except Exception as e:
        print(f"Warning: Could not fetch GitHub token during cold start: {e}")
        
    http_client = httpx.AsyncClient(base_url="https://api.github.com")
    yield
    await http_client.aclose()

app = FastAPI(lifespan=lifespan)

def build_headers(token: str) -> dict:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def format_error(message: str, status_code: int) -> dict:
    return {
        "error": message,
        "github_status": status_code
    }

def check_rate_limit(response: httpx.Response, result: dict):
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) < 100:
        result["rate_limit_warning"] = True

async def github_request(method: str, path: str, **kwargs) -> tuple[dict, int, httpx.Response]:
    token = get_github_token()
    headers = build_headers(token)
    
    response = await http_client.request(method, path, headers=headers, **kwargs)
    
    # Handle token expiration / 401
    if response.status_code == 401:
        token = get_github_token(force_refresh=True)
        headers = build_headers(token)
        response = await http_client.request(method, path, headers=headers, **kwargs)

    try:
        data = response.json()
    except Exception:
        data = {"message": response.text}
        
    return data, response.status_code, response

# --- Models ---

class ReadIssuesInput(BaseModel):
    repo: str
    state: str = "open"
    labels: Optional[List[str]] = None
    limit: int = 25

class ReadPullRequestsInput(BaseModel):
    repo: str
    state: str = "open"
    limit: int = 25

class ReadCiStatusInput(BaseModel):
    repo: str
    branch: str

class CreateIssueInput(BaseModel):
    repo: str
    title: str
    body: str
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None

class CreateBranchInput(BaseModel):
    repo: str
    branch_name: str
    from_branch: str = "main"

class PostCommentInput(BaseModel):
    repo: str
    issue_or_pr_number: int
    body: str

class ReadCommitsInput(BaseModel):
    repo: str
    branch: str = "main"
    limit: int = 20

# --- Endpoints ---

@app.post("/services/mcp/github/read_issues")
async def read_issues(input_data: ReadIssuesInput):
    params = {"state": input_data.state, "per_page": input_data.limit}
    if input_data.labels:
        params["labels"] = ",".join(input_data.labels)
        
    data, status, resp = await github_request("GET", f"/repos/{input_data.repo}/issues", params=params)
    
    if status != 200:
        return format_error(data.get("message", "Failed to read issues"), status)
        
    issues = []
    for item in data:
        # Skip pull requests (GitHub API returns PRs in issues endpoint)
        if "pull_request" in item:
            continue
        issues.append({
            "id": item.get("id"),
            "number": item.get("number"),
            "title": item.get("title"),
            "body": item.get("body"),
            "state": item.get("state"),
            "labels": [lbl.get("name") for lbl in item.get("labels", [])],
            "assignees": [a.get("login") for a in item.get("assignees", [])],
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "url": item.get("html_url")
        })
        
    result = {"result": issues[:input_data.limit]}
    check_rate_limit(resp, result)
    return result

@app.post("/services/mcp/github/read_pull_requests")
async def read_pull_requests(input_data: ReadPullRequestsInput):
    params = {"state": input_data.state, "per_page": input_data.limit}
    data, status, resp = await github_request("GET", f"/repos/{input_data.repo}/pulls", params=params)
    
    if status != 200:
        return format_error(data.get("message", "Failed to read pull requests"), status)
        
    prs = []
    for item in data:
        # Simple fetch of CI status logic here might be too heavy for a list, so we leave it as pending or mock
        # Real implementation would call /commits/{sha}/check-runs for each, but we'll leave as unknown per schema
        prs.append({
            "id": item.get("id"),
            "number": item.get("number"),
            "title": item.get("title"),
            "body": item.get("body"),
            "state": item.get("state"),
            "head_branch": item.get("head", {}).get("ref"),
            "base_branch": item.get("base", {}).get("ref"),
            "author": item.get("user", {}).get("login"),
            "reviewers": [r.get("login") for r in item.get("requested_reviewers", [])],
            "ci_status": "unknown", # To get this accurately requires N API calls
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "url": item.get("html_url")
        })
        
    result = {"result": prs}
    check_rate_limit(resp, result)
    return result

@app.post("/services/mcp/github/read_ci_status")
async def read_ci_status(input_data: ReadCiStatusInput):
    # Fetch check runs for the branch
    data, status, resp = await github_request("GET", f"/repos/{input_data.repo}/commits/{input_data.branch}/check-runs")
    
    if status != 200:
        return format_error(data.get("message", "Failed to read CI status"), status)
        
    check_runs = data.get("check_runs", [])
    overall_status = "success"
    if not check_runs:
        overall_status = "unknown"
    else:
        for run in check_runs:
            if run.get("status") != "completed":
                overall_status = "pending"
                break
            if run.get("conclusion") in ["failure", "timed_out", "action_required", "cancelled"]:
                overall_status = "failure"
                break
                
    runs = [{
        "name": run.get("name"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "url": run.get("html_url"),
        "updated_at": run.get("completed_at") or run.get("started_at")
    } for run in check_runs]
    
    result = {"result": {"branch": input_data.branch, "status": overall_status, "workflow_runs": runs}}
    check_rate_limit(resp, result)
    return result

@app.post("/services/mcp/github/create_issue")
async def create_issue(input_data: CreateIssueInput):
    payload = {
        "title": input_data.title,
        "body": input_data.body
    }
    if input_data.labels:
        payload["labels"] = input_data.labels
    if input_data.assignees:
        payload["assignees"] = input_data.assignees
        
    data, status, resp = await github_request("POST", f"/repos/{input_data.repo}/issues", json=payload)
    
    if status not in (200, 201):
        return format_error(data.get("message", "Failed to create issue"), status)
        
    res_data = {
        "id": data.get("id"),
        "number": data.get("number"),
        "url": data.get("html_url"),
        "title": data.get("title"),
        "state": data.get("state")
    }
    result = {"result": res_data}
    check_rate_limit(resp, result)
    return result

@app.post("/services/mcp/github/create_branch")
async def create_branch(input_data: CreateBranchInput):
    # First get the SHA of the from_branch
    ref_data, status, ref_resp = await github_request("GET", f"/repos/{input_data.repo}/git/ref/heads/{input_data.from_branch}")
    
    if status != 200:
        return format_error(ref_data.get("message", "Failed to get base branch SHA"), status)
        
    sha = ref_data.get("object", {}).get("sha")
    
    # Create the new branch reference
    payload = {
        "ref": f"refs/heads/{input_data.branch_name}",
        "sha": sha
    }
    data, status, resp = await github_request("POST", f"/repos/{input_data.repo}/git/refs", json=payload)
    
    if status not in (200, 201):
        return format_error(data.get("message", "Failed to create branch"), status)
        
    res_data = {
        "branch_name": input_data.branch_name,
        "sha": data.get("object", {}).get("sha"),
        "url": data.get("url") # Note: This is API URL, html_url isn't directly returned here
    }
    result = {"result": res_data}
    check_rate_limit(resp, result)
    return result

@app.post("/services/mcp/github/post_comment")
async def post_comment(input_data: PostCommentInput):
    payload = {
        "body": input_data.body
    }
    data, status, resp = await github_request("POST", f"/repos/{input_data.repo}/issues/{input_data.issue_or_pr_number}/comments", json=payload)
    
    if status not in (200, 201):
        return format_error(data.get("message", "Failed to post comment"), status)
        
    res_data = {
        "comment_id": data.get("id"),
        "url": data.get("html_url"),
        "created_at": data.get("created_at")
    }
    result = {"result": res_data}
    check_rate_limit(resp, result)
    return result

@app.post("/services/mcp/github/read_commits")
async def read_commits(input_data: ReadCommitsInput):
    params = {"sha": input_data.branch, "per_page": input_data.limit}
    data, status, resp = await github_request("GET", f"/repos/{input_data.repo}/commits", params=params)
    
    if status != 200:
        return format_error(data.get("message", "Failed to read commits"), status)
        
    commits = []
    for item in data:
        commit_info = item.get("commit", {})
        commits.append({
            "sha": item.get("sha"),
            "message": commit_info.get("message"),
            "author": commit_info.get("author", {}).get("name"),
            "timestamp": commit_info.get("author", {}).get("date"),
            "url": item.get("html_url"),
            # Files changed requires fetching the individual commit
            "files_changed": [] 
        })
        
    result = {"result": commits}
    check_rate_limit(resp, result)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
