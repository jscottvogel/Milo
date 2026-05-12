import logging
import httpx
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

logger = logging.getLogger(__name__)

MCP_URL = "http://127.0.0.1:8000/v1/github"

class GithubReadInput(BaseModel):
    action: str = Field(description="The read action to perform: 'read_issues', 'read_pull_requests', 'read_ci_status', or 'read_commits'")
    repo: str = Field(description="The GitHub repository in 'owner/repo' format")
    state: str = Field(default="open", description="State filter for issues or PRs ('open', 'closed', 'all')")
    branch: Optional[str] = Field(default=None, description="The branch name, required for 'read_ci_status' or 'read_commits'")
    labels: Optional[List[str]] = Field(default=None, description="List of labels to filter issues by")
    limit: int = Field(default=25, description="Maximum number of items to return")

class GithubReadOutput(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

class GithubReadTool(Tool):
    name = "github__read"
    description = "Read information from GitHub, including issues, pull requests, CI status, and commits."
    input_schema = GithubReadInput
    output_schema = GithubReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        action = input_data["action"]
        valid_actions = ["read_issues", "read_pull_requests", "read_ci_status", "read_commits"]
        
        if action not in valid_actions:
            return GithubReadOutput(success=False, data=None, error=f"Invalid action. Must be one of {valid_actions}").model_dump()
            
        endpoint = f"{MCP_URL}/{action}"
        
        # Build payload matching the MCP input schema
        payload = {"repo": input_data["repo"]}
        if action in ["read_issues", "read_pull_requests"]:
            payload["state"] = input_data.get("state", "open")
            payload["limit"] = input_data.get("limit", 25)
            if action == "read_issues" and input_data.get("labels"):
                payload["labels"] = input_data["labels"]
        elif action in ["read_ci_status", "read_commits"]:
            if not input_data.get("branch"):
                return GithubReadOutput(success=False, data=None, error="branch is required for this action").model_dump()
            payload["branch"] = input_data["branch"]
            if action == "read_commits":
                payload["limit"] = input_data.get("limit", 20)

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer dev_{context.tenant_id}"}
                resp = await client.post(endpoint, json=payload, headers=headers, timeout=15.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return GithubReadOutput(success=True, data=data.get("result")).model_dump()
                else:
                    return GithubReadOutput(success=False, data=None, error=resp.text).model_dump()
        except Exception as e:
            logger.error(f"Error calling GitHub MCP {action}: {e}")
            return GithubReadOutput(success=False, data=None, error=str(e)).model_dump()

class GithubWriteInput(BaseModel):
    action: str = Field(description="The write action to perform: 'create_issue', 'create_branch', or 'post_comment'")
    repo: str = Field(description="The GitHub repository in 'owner/repo' format")
    # create_issue fields
    title: Optional[str] = Field(default=None, description="Issue title")
    body: Optional[str] = Field(default=None, description="Issue or comment body")
    labels: Optional[List[str]] = Field(default=None, description="List of labels for the issue")
    assignees: Optional[List[str]] = Field(default=None, description="List of assignees for the issue")
    # create_branch fields
    branch_name: Optional[str] = Field(default=None, description="The name of the new branch")
    from_branch: Optional[str] = Field(default="main", description="The base branch to branch off of")
    # post_comment fields
    issue_or_pr_number: Optional[int] = Field(default=None, description="The issue or PR number to comment on")

class GithubWriteOutput(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None

class GithubWriteTool(Tool):
    name = "github__write"
    description = "Write data to GitHub, including creating issues, branching, and posting PR/issue comments."
    input_schema = GithubWriteInput
    output_schema = GithubWriteOutput
    mutates = True
    requires_approval = True  # We generally want approval before mutating GitHub

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        action = input_data["action"]
        valid_actions = ["create_issue", "create_branch", "post_comment"]
        
        if action not in valid_actions:
            return GithubWriteOutput(success=False, data=None, error=f"Invalid action. Must be one of {valid_actions}").model_dump()
            
        endpoint = f"{MCP_URL}/{action}"
        payload = {"repo": input_data["repo"]}
        
        if action == "create_issue":
            if not input_data.get("title") or not input_data.get("body"):
                return GithubWriteOutput(success=False, data=None, error="title and body are required to create an issue").model_dump()
            payload["title"] = input_data["title"]
            payload["body"] = input_data["body"]
            if input_data.get("labels"):
                payload["labels"] = input_data["labels"]
            if input_data.get("assignees"):
                payload["assignees"] = input_data["assignees"]
        elif action == "create_branch":
            if not input_data.get("branch_name"):
                return GithubWriteOutput(success=False, data=None, error="branch_name is required to create a branch").model_dump()
            payload["branch_name"] = input_data["branch_name"]
            payload["from_branch"] = input_data.get("from_branch", "main")
        elif action == "post_comment":
            if not input_data.get("body") or not input_data.get("issue_or_pr_number"):
                return GithubWriteOutput(success=False, data=None, error="body and issue_or_pr_number are required to post a comment").model_dump()
            payload["body"] = input_data["body"]
            payload["issue_or_pr_number"] = input_data["issue_or_pr_number"]

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer dev_{context.tenant_id}"}
                resp = await client.post(endpoint, json=payload, headers=headers, timeout=15.0)
                
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return GithubWriteOutput(success=True, data=data.get("result")).model_dump()
                else:
                    return GithubWriteOutput(success=False, data=None, error=resp.text).model_dump()
        except Exception as e:
            logger.error(f"Error calling GitHub MCP {action}: {e}")
            return GithubWriteOutput(success=False, data=None, error=str(e)).model_dump()
