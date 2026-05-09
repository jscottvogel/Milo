# GitHub MCP Tool Integration for Milo

**Date:** 2026-05-08T21:45:17.696860
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description

Milo needs a GitHub tool integration (`github__tool`) that follows the same MCP server pattern as existing integrations (email, calendar, Nylas, etc.). 

Currently Milo tracks the *plan* (work items, milestones, risks) but is completely blind to the *build* happening in GitHub. This integration closes that gap — allowing Milo to self-monitor the Milo platform codebase, link program work items to real commits/PRs, surface CI failures as risks, and auto-create GitHub issues from engineering handoff documents.

The tool should be exposed to the Milo agent as a set of callable functions (tools) via the existing MCP tool registration pattern. Authentication should use a GitHub Personal Access Token (PAT) or GitHub App credentials stored in the tenant secrets store, consistent with how Nylas OAuth tokens are stored today.

**Primary use cases:**
1. Milo reads open issues and PRs to monitor build progress on its own platform
2. Every `developer__handoff` Milo files auto-creates a corresponding GitHub issue in the correct repo
3. Milo reads CI/CD run status and surfaces failures as program risks automatically
4. Milo can create a branch following the `phase/<n>-<slug>` naming convention when a new phase kicks off
5. Milo can post a comment on a PR when it detects spec drift between the PR diff and the filed requirements doc
6. Work items in Milo's tracker can be linked to GitHub commits/PRs via metadata


## Acceptance Criteria
- [ ] A `github__read_issues` tool function is registered and callable by the Milo agent, returning id, title, body, state, labels, assignees, created_at, updated_at for a given repo
- [ ] A `github__read_pull_requests` tool function is registered and callable, returning id, title, body, state, head_branch, base_branch, ci_status, created_at, updated_at
- [ ] A `github__read_ci_status` tool function is registered and callable, returning the latest workflow run status (success/failure/in_progress) for a given repo and branch
- [ ] A `github__create_issue` tool function is registered and callable, accepting title, body, labels (array), and assignees (array), and returning the created issue URL and id
- [ ] A `github__create_branch` tool function is registered and callable, accepting branch_name and base_branch, creating the branch in the target repo
- [ ] A `github__post_comment` tool function is registered and callable, accepting issue_or_pr_number and comment_body, posting the comment to the correct thread
- [ ] A `github__read_commits` tool function is registered and callable, returning the last N commits for a given branch with sha, message, author, and timestamp
- [ ] Authentication is handled via GitHub PAT stored in the tenant secrets store — no credentials are hardcoded
- [ ] Target repo is configurable per-tenant via an environment variable or tenant config (e.g. `GITHUB_DEFAULT_REPO`)
- [ ] All tool functions follow the existing MCP input/output schema pattern (title, description, parameters as JSON Schema)
- [ ] When `developer__handoff` is called by Milo, a GitHub issue is automatically created in the configured repo using `github__create_issue` with the handoff title and description as the issue body
- [ ] CI failure on the main or active phase branch triggers Milo to create a risk work item via `work_item__update` with likelihood=4, impact=4, and a mitigation note linking to the failed run URL
- [ ] Integration is covered by at least one end-to-end test: Milo reads a real (or mocked) GitHub issue and surfaces it in a work item update

## Technical Notes

**Architecture pattern:**
- Follow the same MCP server structure as `/services/mcp/nylas` — a lightweight FastAPI or Lambda handler that wraps the GitHub REST API (or PyGitHub / octokit) and exposes tool definitions
- Register tools in the same tool catalog used by the LangGraph agent (Phase 3-4 workstream)
- Use `httpx` or `PyGitHub` (`pip install PyGitHub`) for API calls
- GitHub API base: `https://api.github.com`
- Auth header: `Authorization: Bearer <PAT>` or GitHub App JWT

**Suggested tool registration name prefix:** `github__`

**Secrets store key:** `GITHUB_PAT` (or `GITHUB_APP_PRIVATE_KEY` + `GITHUB_APP_ID` if using GitHub App auth — preferred for production)

**Default repo config:** `GITHUB_DEFAULT_REPO=org/repo` in tenant environment config

**Rate limiting:** GitHub REST API allows 5,000 requests/hour for authenticated requests — add a simple retry/backoff wrapper

**Phase branch naming convention already in use:** `phase/<n>-<slug>` (e.g. `phase/3-agent-runtime`) — `github__create_branch` should validate this pattern

**Spec drift detection (stretch goal):** When Milo calls `github__read_pull_requests`, compare the PR's changed files against the `technical_notes` field of the corresponding `developer__handoff` doc stored in tenant storage. Flag mismatches as a comment on the PR.

**Priority order for implementation:**
1. `github__read_issues` + `github__create_issue` (highest value, unblocks handoff auto-linking)
2. `github__read_ci_status` (unblocks risk auto-creation on CI failure)
3. `github__read_pull_requests` + `github__post_comment`
4. `github__create_branch` + `github__read_commits`

