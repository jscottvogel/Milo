# External System Webhooks — GitHub, Slack, and Jira Integration via MCP

**Date:** 2026-05-10T14:14:30.111903
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently has no integration with external development and communication tools. There is an open work item (ID: 56bf160e) to build a GitHub MCP server integration. This capability expands that to a full External System Webhooks layer covering GitHub, Slack, and Jira. Milo should be able to: (1) receive inbound webhooks from these systems and translate them into work item updates or risk flags, (2) post outbound messages/comments to these systems from the agent loop, and (3) auto-create GitHub issues from developer handoffs. This closes the P3 gap in the 20-capability target list and fulfills the open GitHub MCP task.

## Acceptance Criteria
- [ ] github__read tool registered in Bedrock payload — reads issues, PRs, CI status for a given repo
- [ ] github__write tool registered in Bedrock payload — creates issues, posts PR comments, creates branches
- [ ] Milo auto-creates a GitHub issue when developer__handoff is called (if GitHub integration is configured for the tenant)
- [ ] slack__send tool registered in Bedrock payload — posts a message to a configured Slack channel
- [ ] Milo posts to Slack when a critical risk is flagged or a milestone is overdue (if Slack integration configured)
- [ ] jira__read tool registered in Bedrock payload — reads issues and sprint status for a configured Jira project
- [ ] jira__write tool registered in Bedrock payload — creates and updates Jira issues
- [ ] Inbound webhook endpoint POST /webhooks/{source} (source: github | slack | jira) receives events and routes to Milo agent loop
- [ ] GitHub webhook: PR merged → auto-update linked task status to 'complete'
- [ ] Jira webhook: issue status change → sync to linked Milo work item status
- [ ] All integrations are tenant-configurable (on/off per integration, per tenant) via Settings
- [ ] OAuth or API key credential storage is encrypted at rest (AWS Secrets Manager)
- [ ] End-to-end test: GitHub issue created from a developer__handoff call, confirmed in GitHub API
- [ ] Closes open work item 56bf160e (Build GitHub MCP Tool for Milo)

## Technical Notes
Architecture: MCP (Model Context Protocol) server pattern for GitHub (as per existing work item 56bf160e). Slack: use Slack Bolt SDK or direct Web API. Jira: Jira REST API v3. Inbound webhooks: FastAPI POST /webhooks/{source} endpoint, verified via HMAC signature. Outbound: tools registered in tools_config.py. Credential storage: AWS Secrets Manager, one secret per tenant per integration. Tenant settings: add integration_config JSONB column to tenants table. Priority: P3. Supersedes/closes work item 56bf160e.
