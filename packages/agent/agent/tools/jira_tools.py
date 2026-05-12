import logging
import httpx
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field
import base64

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

logger = logging.getLogger(__name__)

class JiraReadInput(BaseModel):
    action: str = Field(description="The read action to perform: 'get_issue' or 'search_issues'")
    issue_key: Optional[str] = Field(default=None, description="The Jira issue key (e.g., 'PROJ-123') required for 'get_issue'")
    jql: Optional[str] = Field(default=None, description="Jira Query Language string required for 'search_issues'")
    max_results: int = Field(default=50, description="Maximum number of issues to return")

class JiraReadOutput(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

class JiraReadTool(Tool):
    name = "jira.read"
    description = "Read information from Jira, including specific issues or searching via JQL."
    input_schema = JiraReadInput
    output_schema = JiraReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        token = context.integration_tokens.get("jira_api_token")
        email = context.integration_tokens.get("jira_email")
        domain = context.integration_tokens.get("jira_domain") # e.g., 'your-domain.atlassian.net'
        
        if not token or not email or not domain:
            return JiraReadOutput(
                success=False, 
                data=None, 
                error="Jira integration is not fully configured (missing token, email, or domain)."
            ).model_dump()
            
        auth_string = f"{email}:{token}"
        auth_header = f"Basic {base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')}"
        headers = {
            "Authorization": auth_header,
            "Accept": "application/json"
        }
        
        base_url = f"https://{domain}/rest/api/3"
        action = input_data["action"]
        
        try:
            async with httpx.AsyncClient() as client:
                if action == "get_issue":
                    if not input_data.get("issue_key"):
                        return JiraReadOutput(success=False, data=None, error="issue_key is required for get_issue").model_dump()
                    
                    resp = await client.get(f"{base_url}/issue/{input_data['issue_key']}", headers=headers, timeout=15.0)
                elif action == "search_issues":
                    if not input_data.get("jql"):
                        return JiraReadOutput(success=False, data=None, error="jql is required for search_issues").model_dump()
                        
                    params = {
                        "jql": input_data["jql"],
                        "maxResults": input_data.get("max_results", 50)
                    }
                    resp = await client.get(f"{base_url}/search", params=params, headers=headers, timeout=15.0)
                else:
                    return JiraReadOutput(success=False, data=None, error=f"Invalid action: {action}").model_dump()
                
                if resp.status_code == 200:
                    return JiraReadOutput(success=True, data=resp.json()).model_dump()
                else:
                    return JiraReadOutput(success=False, data=None, error=f"Jira API error {resp.status_code}: {resp.text}").model_dump()
        except Exception as e:
            logger.error(f"Error calling Jira read API: {e}")
            return JiraReadOutput(success=False, data=None, error=str(e)).model_dump()

class JiraWriteInput(BaseModel):
    action: str = Field(description="The write action to perform: 'create_issue' or 'update_issue'")
    # Create / Update fields
    project_key: Optional[str] = Field(default=None, description="Jira project key (e.g., 'PROJ') for creating issues")
    issue_type: Optional[str] = Field(default="Task", description="Jira issue type (e.g., 'Bug', 'Task')")
    summary: Optional[str] = Field(default=None, description="Issue summary/title")
    description: Optional[str] = Field(default=None, description="Issue description text")
    issue_key: Optional[str] = Field(default=None, description="The Jira issue key required for 'update_issue'")
    transition_id: Optional[str] = Field(default=None, description="Optional transition ID to move the issue to a new status")

class JiraWriteOutput(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

class JiraWriteTool(Tool):
    name = "jira.write"
    description = "Write data to Jira, including creating new issues and updating existing ones (e.g., changing status)."
    input_schema = JiraWriteInput
    output_schema = JiraWriteOutput
    mutates = True
    requires_approval = True

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        token = context.integration_tokens.get("jira_api_token")
        email = context.integration_tokens.get("jira_email")
        domain = context.integration_tokens.get("jira_domain")
        
        if not token or not email or not domain:
            return JiraWriteOutput(success=False, data=None, error="Jira integration is not configured.").model_dump()
            
        auth_string = f"{email}:{token}"
        auth_header = f"Basic {base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')}"
        headers = {
            "Authorization": auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        base_url = f"https://{domain}/rest/api/3"
        action = input_data["action"]
        
        try:
            async with httpx.AsyncClient() as client:
                if action == "create_issue":
                    if not input_data.get("project_key") or not input_data.get("summary"):
                        return JiraWriteOutput(success=False, data=None, error="project_key and summary are required to create an issue").model_dump()
                        
                    payload: Dict[str, Any] = {
                        "fields": {
                            "project": {"key": input_data["project_key"]},
                            "summary": input_data["summary"],
                            "issuetype": {"name": input_data.get("issue_type", "Task")}
                        }
                    }
                    if input_data.get("description"):
                        # Jira v3 requires Atlassian Document Format (ADF)
                        payload["fields"]["description"] = {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": input_data["description"]}
                                    ]
                                }
                            ]
                        }
                    
                    resp = await client.post(f"{base_url}/issue", json=payload, headers=headers, timeout=15.0)
                    if resp.status_code == 201:
                        return JiraWriteOutput(success=True, data=resp.json()).model_dump()
                    else:
                        return JiraWriteOutput(success=False, data=None, error=f"Failed to create issue: {resp.text}").model_dump()
                        
                elif action == "update_issue":
                    if not input_data.get("issue_key"):
                        return JiraWriteOutput(success=False, data=None, error="issue_key is required to update an issue").model_dump()
                        
                    # Handle status transition if provided
                    if input_data.get("transition_id"):
                        transition_payload = {"transition": {"id": input_data["transition_id"]}}
                        resp = await client.post(f"{base_url}/issue/{input_data['issue_key']}/transitions", json=transition_payload, headers=headers, timeout=15.0)
                        if resp.status_code not in (204, 200):
                            return JiraWriteOutput(success=False, data=None, error=f"Failed to transition issue: {resp.text}").model_dump()
                            
                    # Update fields if provided (simplified)
                    update_fields = {}
                    if input_data.get("summary"):
                        update_fields["summary"] = input_data["summary"]
                        
                    if update_fields:
                        payload = {"fields": update_fields}
                        resp = await client.put(f"{base_url}/issue/{input_data['issue_key']}", json=payload, headers=headers, timeout=15.0)
                        if resp.status_code not in (204, 200):
                            return JiraWriteOutput(success=False, data=None, error=f"Failed to update issue fields: {resp.text}").model_dump()
                            
                    return JiraWriteOutput(success=True, data={"message": "Issue updated successfully"}).model_dump()
                else:
                    return JiraWriteOutput(success=False, data=None, error=f"Invalid action: {action}").model_dump()

        except Exception as e:
            logger.error(f"Error calling Jira write API: {e}")
            return JiraWriteOutput(success=False, data=None, error=str(e)).model_dump()
