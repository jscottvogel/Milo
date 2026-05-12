# External System Integrations — Fix Backend Wiring for github__read, github__write, jira__read, jira__write, slack__send

**Date:** 2026-05-12T09:05:36.392844
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Five external integration tools are registered in the Bedrock tool payload but all return "Tool not found" when called by Milo. This was confirmed on 2026-05-14 during a full capability sweep. The tools were originally spec'd and handed off on 2026-05-10 but have not been wired to live backend handlers.

**Broken Tools (all returning "Tool not found"):**
1. `github__read` — Read GitHub issues, PRs, CI status, commits
2. `github__write` — Create GitHub issues, branches, post PR comments
3. `jira__read` — Read Jira issues via JQL or issue key
4. `jira__write` — Create/update Jira issues
5. `slack__send` — Send messages to Slack channels

**What Each Tool Must Do:**

### github__read
- Parameters: action ('read_issues' | 'read_pull_requests' | 'read_ci_status' | 'read_commits'), repo (owner/repo), state, labels, branch, limit
- Returns: structured list of issues/PRs/commits/CI runs

### github__write
- Parameters: action ('create_issue' | 'create_branch' | 'post_comment'), repo, title, body, labels, assignees, branch_name, from_branch, issue_or_pr_number
- Returns: created/updated resource URL and ID

### jira__read
- Parameters: action ('get_issue' | 'search_issues'), issue_key, jql, max_results
- Returns: structured issue data

### jira__write
- Parameters: action ('create_issue' | 'update_issue'), project_key, summary, description, issue_type, issue_key, transition_id
- Returns: created/updated issue key and URL

### slack__send
- Parameters: channel (channel ID or name), text (markdown), blocks (optional Block Kit JSON)
- Returns: message timestamp and channel

**Integration Architecture:**
- GitHub: PyGithub or httpx + GitHub REST API v3. Auth: GitHub Personal Access Token or GitHub App, stored in AWS Secrets Manager per tenant.
- Jira: Jira REST API v3 (Atlassian Cloud). Auth: API token + email, stored in AWS Secrets Manager per tenant.
- Slack: Slack Web API (slack_sdk). Auth: Bot OAuth token, stored in AWS Secrets Manager per tenant.
- All credentials: one secret per tenant per integration in AWS Secrets Manager. Key format: `milo/{tenant_id}/github`, `milo/{tenant_id}/jira`, `milo/{tenant_id}/slack`
- Tenant settings: `integration_config` JSONB column on tenants table — stores which integrations are enabled per tenant.

**Root Cause of Current Failure:**
Tools are in the Bedrock payload schema but FastAPI routes and/or Bedrock tool dispatch handlers are missing or misnamed. Confirm all tool names use double-underscore convention.

## Acceptance Criteria
- [ ] github__read callable by Milo — reads issues, PRs, CI status, commits from a configured GitHub repo
- [ ] github__write callable by Milo — creates issues, creates branches, posts PR comments
- [ ] jira__read callable by Milo — reads issues by key and searches via JQL
- [ ] jira__write callable by Milo — creates and updates Jira issues
- [ ] slack__send callable by Milo — posts messages to a configured Slack channel
- [ ] All 5 tools registered in Bedrock payload with correct double-underscore naming
- [ ] Credentials stored in AWS Secrets Manager — one secret per tenant per integration
- [ ] integration_config JSONB column on tenants table — controls which integrations are enabled
- [ ] All tools gracefully return a clear error message if the integration is not configured for the tenant (no crash)
- [ ] Milo auto-creates a GitHub issue when developer__handoff is called (if GitHub integration is configured for tenant)
- [ ] Milo posts to Slack when a critical risk is flagged or a milestone is overdue (if Slack configured)
- [ ] Unit tests for each tool: happy path + unconfigured tenant path
- [ ] End-to-end test: github__read returns real issues from a test repo
- [ ] End-to-end test: slack__send posts a message to a test channel
- [ ] No mock data in any production code path
- [ ] Closes open work item 56bf160e (Build GitHub MCP Tool for Milo)

## Technical Notes
CRITICAL: All 5 tools are returning 'Tool not found' — this is a naming/registration bug. Confirm all tool handler keys use double underscores (github__read, github__write, jira__read, jira__write, slack__send), not dot notation. Check tools_config.py and the Lambda tool dispatch table. FastAPI routers may be missing entirely — check app/routers/ for github.py, jira.py, slack.py. If absent, create them. Use PyGithub or httpx for GitHub, atlassian-python-api or httpx for Jira, slack_sdk for Slack. All secrets via boto3 SecretsManager client. Do NOT hardcode any credentials. Tenant isolation required on all routes.
