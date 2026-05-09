# GitHub MCP Integration

The GitHub Model Context Protocol (MCP) service provides a secure, isolated set of API endpoints for the LangGraph agent to interact with GitHub repositories on behalf of the configured tenant.

## Overview

- **Location**: `services/mcp/github/`
- **Runtime**: FastAPI
- **Authentication**: Fetches GitHub Personal Access Token (PAT) from AWS Secrets Manager (`milo/github/token`), caches it in-memory, and automatically refreshes upon a 401 response.
- **Tenant Isolation**: Tool callers are required to provide the correct GitHub org/repo based on the active user's `tenant_settings`.

## Endpoints

All endpoints are `POST` requests under `/services/mcp/github/` and expect a JSON payload.

| Endpoint | Description | Input Params |
| --- | --- | --- |
| `/read_issues` | Fetch open/closed issues | `repo`, `state`, `labels`, `limit` |
| `/read_pull_requests` | Fetch open/closed/merged PRs | `repo`, `state`, `limit` |
| `/read_ci_status` | Get CI check runs for a branch | `repo`, `branch` |
| `/create_issue` | Create a new issue | `repo`, `title`, `body`, `labels`, `assignees` |
| `/create_branch` | Branch off from an existing branch | `repo`, `branch_name`, `from_branch` |
| `/post_comment` | Post a comment on an issue or PR | `repo`, `issue_or_pr_number`, `body` |
| `/read_commits` | Fetch recent commits on a branch | `repo`, `branch`, `limit` |

## Rate Limits & Error Handling

- **Rate Limits**: The service checks the `X-RateLimit-Remaining` header. If it drops below 100, the response payload will include `"rate_limit_warning": true`.
- **Errors**: Native exceptions are caught. The service returns a structured dictionary for all GitHub API errors:
  ```json
  {
    "error": "Not Found",
    "github_status": 404
  }
  ```

## Infrastructure

The CDK construct `GitHubMcpConstruct` located in `cdk/constructs/github_mcp_construct.py` sets up the Lambda function, API Gateway, and grants the Lambda execution role `secretsmanager:GetSecretValue` for the secret.

## Auto-Issue Creation Hook

When the LangGraph runtime executes the `developer.handoff` tool to generate technical specifications:
1. It writes the Markdown document.
2. It fetches the tenant's default GitHub repository and assignee.
3. It performs an asynchronous `httpx` POST to the MCP `/create_issue` endpoint.
4. The issue is assigned to the configured engineer and labeled with `milo-handoff`.
