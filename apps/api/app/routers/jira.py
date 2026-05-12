import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx
import boto3

router = APIRouter(prefix="/v1/jira", tags=["Jira"])

_REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")

def get_jira_credentials(tenant_id: str) -> Optional[Dict[str, str]]:
    secret_name = f"milo/{tenant_id}/jira"
    try:
        client = boto3.client('secretsmanager', region_name=_REGION_NAME)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get('SecretString', '')
        import json
        secret_dict = json.loads(secret_string)
        if "jira_domain" in secret_dict and "jira_email" in secret_dict and "jira_token" in secret_dict:
            return secret_dict
        return None
    except Exception as e:
        return None

def get_tenant_id_from_request(request: Request) -> str:
    context = getattr(request.state, "auth_context", None)
    if context:
        return context.tenant_id
    return None

def build_auth(creds: dict):
    import base64
    auth_str = f"{creds['jira_email']}:{creds['jira_token']}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64_auth}", "Accept": "application/json"}

# --- Models ---
class GetIssueInput(BaseModel):
    issue_key: str

class SearchIssuesInput(BaseModel):
    jql: str
    max_results: int = 50

class CreateIssueInput(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: str = "Task"

class UpdateIssueInput(BaseModel):
    issue_key: str
    summary: Optional[str] = None
    description: Optional[str] = None
    transition_id: Optional[str] = None

# --- Endpoints ---

@router.post("/get_issue")
async def get_issue(request: Request, input_data: GetIssueInput):
    tenant_id = get_tenant_id_from_request(request)
    creds = get_jira_credentials(tenant_id)
    if not creds:
        return {"success": False, "error": "Jira integration is not configured for this tenant."}
        
    domain = creds["jira_domain"].rstrip("/")
    url = f"{domain}/rest/api/3/issue/{input_data.issue_key}"
    headers = build_auth(creds)
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return {"success": True, "result": resp.json()}
        else:
            return {"success": False, "error": f"Jira API Error: {resp.text}"}

@router.post("/search_issues")
async def search_issues(request: Request, input_data: SearchIssuesInput):
    tenant_id = get_tenant_id_from_request(request)
    creds = get_jira_credentials(tenant_id)
    if not creds:
        return {"success": False, "error": "Jira integration is not configured for this tenant."}
        
    domain = creds["jira_domain"].rstrip("/")
    url = f"{domain}/rest/api/3/search"
    headers = build_auth(creds)
    payload = {
        "jql": input_data.jql,
        "maxResults": input_data.max_results
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            return {"success": True, "result": resp.json().get("issues", [])}
        else:
            return {"success": False, "error": f"Jira API Error: {resp.text}"}

@router.post("/create_issue")
async def create_issue(request: Request, input_data: CreateIssueInput):
    tenant_id = get_tenant_id_from_request(request)
    creds = get_jira_credentials(tenant_id)
    if not creds:
        return {"success": False, "error": "Jira integration is not configured for this tenant."}
        
    domain = creds["jira_domain"].rstrip("/")
    url = f"{domain}/rest/api/3/issue"
    headers = build_auth(creds)
    payload = {
        "fields": {
            "project": {"key": input_data.project_key},
            "summary": input_data.summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": input_data.description}]}]
            },
            "issuetype": {"name": input_data.issue_type}
        }
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 201:
            data = resp.json()
            data["url"] = f"{domain}/browse/{data['key']}"
            return {"success": True, "result": data}
        else:
            return {"success": False, "error": f"Jira API Error: {resp.text}"}

@router.post("/update_issue")
async def update_issue(request: Request, input_data: UpdateIssueInput):
    tenant_id = get_tenant_id_from_request(request)
    creds = get_jira_credentials(tenant_id)
    if not creds:
        return {"success": False, "error": "Jira integration is not configured for this tenant."}
        
    domain = creds["jira_domain"].rstrip("/")
    headers = build_auth(creds)
    
    # Update fields if provided
    if input_data.summary or input_data.description:
        url = f"{domain}/rest/api/3/issue/{input_data.issue_key}"
        fields = {}
        if input_data.summary:
            fields["summary"] = input_data.summary
        if input_data.description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": input_data.description}]}]
            }
            
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, headers=headers, json={"fields": fields})
            if resp.status_code not in (200, 204):
                return {"success": False, "error": f"Jira API Error updating fields: {resp.text}"}
                
    # Handle transition if provided
    if input_data.transition_id:
        url = f"{domain}/rest/api/3/issue/{input_data.issue_key}/transitions"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json={"transition": {"id": input_data.transition_id}})
            if resp.status_code not in (200, 204):
                return {"success": False, "error": f"Jira API Error executing transition: {resp.text}"}
                
    return {
        "success": True, 
        "result": {
            "issue_key": input_data.issue_key, 
            "url": f"{domain}/browse/{input_data.issue_key}"
        }
    }
