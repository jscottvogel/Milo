# Fix: Register & Deploy 4 Broken Backend Tools — portfolio__read, github__read, jira__read, slack__send

**Date:** 2026-05-12T05:23:43.008427
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Four tools are registered in Milo's Bedrock payload and callable by the agent, but the backend routes/registrations are missing or not deployed. All four return "Tool not found" at runtime. The specs for these tools were filed on 2026-05-10 and code may have been written locally, but the deployed API layer does not reflect them.

**Broken tools:**
1. `portfolio__read` → should call `GET /portfolio`
2. `github__read` → should call `GET /github/...` (MCP pattern)
3. `jira__read` → should call `GET /jira/...`
4. `slack__send` → should call `POST /slack/message`

**Root cause hypothesis:** One or more of the following:
- Routes exist in `main.py` locally but the Lambda/container was not redeployed after the code was written
- Tools are not registered in `tools_config.py` in the deployed package
- Credentials (Secrets Manager) not provisioned for the deployed environment

**Reference specs (already filed):**
- `docs/requests/multi_program_portfolio_view_cross_program_dashboard_and_heatmap_20260510_141427.md`
- `docs/requests/external_system_webhooks_github_slack_and_jira_integration_via_mcp_20260510_141430.md`

## Acceptance Criteria
- [ ] portfolio__read tool returns a valid JSON response (not 'Tool not found') when called by the Milo agent
- [ ] github__read tool returns issues/PRs/CI status for a given repo without error
- [ ] jira__read tool returns issues for a configured Jira project without error
- [ ] slack__send tool successfully posts a message to a configured Slack channel without error
- [ ] All four tools are registered in tools_config.py in the DEPLOYED package (not just local)
- [ ] All four backend routes exist in main.py and are live in the deployed API
- [ ] Required credentials exist in AWS Secrets Manager for the deployed environment
- [ ] No 'Tool not found' errors in CloudWatch logs for any of these four tools after deployment

## Technical Notes
This is a deployment/registration gap, not a new feature build. The code likely already exists locally from the 2026-05-10 aider runs. Steps to verify and fix:
1. Check tools_config.py — confirm all 4 tools are listed with correct route mappings
2. Check main.py — confirm GET /portfolio, GitHub, Jira, and Slack routes exist
3. Run `cdk deploy` or `sam deploy` to push the current local state to AWS
4. Verify AWS Secrets Manager has entries for: GitHub token, Jira API key, Slack bot token (per tenant)
5. Smoke test each tool via the Milo agent after deploy and confirm no 'Tool not found' in CloudWatch logs
