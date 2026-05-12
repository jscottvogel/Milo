# External System Webhooks — GitHub, Slack, and Jira Integration via MCP

**Date:** 2026-05-11T22:01:13.592758
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently has no integration with external development and communication tools. There is an open work item (ID: 56bf160e) to build a GitHub MCP server integration. This capability expands that to a full External System Webhooks layer covering GitHub, Slack, and Jira. Milo should be able to: (1) receive inbound webhooks from these systems and translate them into work item updates or risk flags, (2) post outbound messages/comments to these systems from the agent loop, and (3) auto-create GitHub issues from developer handoffs. This is a P3 gap in the Milo 20-capability target list and closes open work item 56bf160e.

## Acceptance Criteria
- [ ] github__read tool registered in Bedrock payload — reads issues, PRs, CI status for a given repo
- [ ] github__write tool registered — creates issues, posts PR comments, creates branches
- [ ] Milo auto-creates a GitHub issue when developer__handoff is called (if GitHub integration configured for tenant)
- [ ] slack__send tool registered — posts to configured Slack channel
- [ ] Milo posts to Slack when critical risk flagged or milestone overdue
- [ ] jira__read tool registered — reads issues and sprint status for a configured Jira project
- [ ] jira__write tool registered — creates and updates Jira issues
- [ ] POST /webhooks/{source} endpoint receives events and routes to Milo agent loop (source: github | slack | jira)
- [ ] GitHub webhook: PR merged → auto-update linked task to 'complete'
- [ ] Jira webhook: issue status change → sync to linked Milo work item status
- [ ] All integrations tenant-configurable via Settings (on/off per integration, per tenant)
- [ ] Credentials encrypted at rest in AWS Secrets Manager (one secret per tenant per integration)
- [ ] End-to-end test: GitHub issue created from developer__handoff, confirmed in GitHub API
- [ ] Closes open work item 56bf160e (Build GitHub MCP Tool for Milo)
- [ ] HMAC signature verification on all inbound webhook endpoints

## Technical Notes
MCP (Model Context Protocol) server pattern for GitHub (per existing work item 56bf160e). Slack: Slack Bolt SDK or direct Web API. Jira: Jira REST API v3. Credential storage: AWS Secrets Manager, one secret per tenant per integration. Tenant settings: add integration_config JSONB column to tenants table. All integrations tenant-configurable (on/off per integration, per tenant) via Settings. Separate IAM role with least-privilege access to Secrets Manager. Priority: P3.
