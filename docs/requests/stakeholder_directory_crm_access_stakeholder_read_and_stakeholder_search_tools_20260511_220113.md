# Stakeholder Directory & CRM Access — stakeholder__read and stakeholder__search Tools

**Date:** 2026-05-11T22:01:13.588226
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently has a `stakeholder__invite` tool (confirmed live) that can invite stakeholders to programs via email magic link. However, there is no capability to read, search, or query the stakeholder directory. Milo cannot answer questions like "Who are the stakeholders on this program?", "What is the influence/interest level of a given stakeholder?", or "Which stakeholders have not yet accepted their invitation?" This gap means Milo cannot autonomously manage stakeholder engagement, surface disengaged stakeholders in briefings, or reason about stakeholder risk. This is a P2 (High Priority) gap in the Milo 20-capability target list.

## Acceptance Criteria
- [ ] stakeholder__read tool registered in Bedrock payload and callable by Milo
- [ ] stakeholder__read returns all stakeholders for a program_id with full schema: id, program_id, program_name, email, role, influence, interest, satisfaction, status, invited_at, last_active_at
- [ ] stakeholder__read accepts optional filters: program_id, stakeholder_id, status (pending | active | revoked)
- [ ] stakeholder__search tool registered in Bedrock payload and callable by Milo
- [ ] stakeholder__search returns matching stakeholders across all programs for the tenant
- [ ] stakeholder__search accepts filters: query (free-text), role, influence, interest, status, limit (default 20)
- [ ] GET /stakeholders FastAPI endpoint — no mock data
- [ ] GET /stakeholders/search FastAPI endpoint with query param filtering
- [ ] Both endpoints covered by unit tests with seeded data
- [ ] Milo daily briefing includes Stakeholder Health block when any stakeholder pending >7 days
- [ ] Milo hourly monitor flags high-influence stakeholders with satisfaction <= 2 as a risk
- [ ] Both tools respect tenant isolation
- [ ] End-to-end test: stakeholder__read on seeded program returns correct records
- [ ] End-to-end test: stakeholder__search with role='sponsor' returns correct filtered results
- [ ] No breaking changes to stakeholder__invite or work_item__update stakeholder entity type

## Technical Notes
Stakeholders table already exists — linked to work items via parent_id. Add last_active_at column (nullable timestamp) via Alembic migration. email = stakeholder_sub field (already stores email address). Tenant isolation: all queries filter by tenant_id via authenticated request context. Register both tools in tools_config.py (same Bedrock pattern as existing tools). FastAPI router: add stakeholders.py to app/routers/ — GET /stakeholders and GET /stakeholders/search. Do NOT modify stakeholder__invite or existing work_item__update stakeholder path. Priority: P2.
