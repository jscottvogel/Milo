# Stakeholder Directory & CRM Access — stakeholder__read and stakeholder__search Tools

**Date:** 2026-05-10T18:27:50.619328
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently has a `stakeholder__invite` tool (confirmed live 2026-05-10) that can invite stakeholders to programs via email magic link. However, there is no capability to **read, search, or query** the stakeholder directory. Milo cannot answer questions like "Who are the stakeholders on this program?", "What is the influence/interest level of a given stakeholder?", or "Which stakeholders have not yet accepted their invitation?" This gap means Milo cannot autonomously manage stakeholder engagement, surface disengaged stakeholders in briefings, or reason about stakeholder risk.

This handoff defines two new tools — `stakeholder__read` and `stakeholder__search` — backed by FastAPI endpoints that expose the existing `stakeholders` table (already populated by `stakeholder__invite` and `work_item__update` with entity_type='stakeholder').

### Current State
- `stakeholder__invite` tool: LIVE — creates stakeholder records and sends email invitations
- `work_item__update` with `entity_type='stakeholder'`: LIVE — can create/update stakeholder records with fields: stakeholder_sub, role, influence, interest, satisfaction, status
- Stakeholders table: EXISTS in DB, linked to programs via parent_id
- **Missing**: Any read/query capability over this table from the agent loop

### New Tools Required

#### Tool 1: `stakeholder__read`
Read all stakeholders for a given program, or a single stakeholder by ID.

**Parameters:**
- `program_id` (UUID, optional) — returns all stakeholders for the program
- `stakeholder_id` (UUID, optional) — returns a single stakeholder record
- `status` (string, optional) — filter by status: `pending` | `active` | `revoked`

**Returns (per stakeholder):**
```json
{
  "id": "uuid",
  "program_id": "uuid",
  "program_name": "string",
  "email": "string",
  "role": "sponsor | reviewer | observer | ...",
  "influence": "low | med | high",
  "interest": "low | med | high",
  "satisfaction": 1-5 or null,
  "status": "pending | active | revoked",
  "invited_at": "ISO datetime",
  "last_active_at": "ISO datetime or null"
}
```

#### Tool 2: `stakeholder__search`
Search stakeholders across all programs for the tenant by name, email, role, or influence/interest level.

**Parameters:**
- `query` (string, optional) — free-text search against email and role fields
- `role` (string, optional) — filter by role
- `influence` (string, optional) — filter by influence level
- `interest` (string, optional) — filter by interest level
- `status` (string, optional) — filter by status
- `limit` (int, optional, default 20)

**Returns:** Array of stakeholder records (same schema as stakeholder__read)

### Milo Behavioral Changes
Once live, Milo should:
1. Include a "Stakeholder Health" block in the daily briefing when any stakeholder has `status=pending` for >7 days (disengaged invite)
2. Flag stakeholders with `influence=high` and `satisfaction <= 2` as a risk in the hourly monitor loop
3. Answer natural language questions about program stakeholders using stakeholder__read
4. Surface stakeholder engagement gaps in program health assessments

## Acceptance Criteria
- [ ] stakeholder__read tool registered in Bedrock tool payload and callable by Milo
- [ ] stakeholder__read returns all stakeholders for a given program_id with full schema (id, email, role, influence, interest, satisfaction, status, invited_at, last_active_at)
- [ ] stakeholder__read accepts optional filters: program_id, stakeholder_id, status
- [ ] stakeholder__search tool registered in Bedrock tool payload and callable by Milo
- [ ] stakeholder__search returns matching stakeholders across all programs for the tenant
- [ ] stakeholder__search accepts filters: query (free-text), role, influence, interest, status, limit
- [ ] GET /stakeholders FastAPI endpoint backed by stakeholders table — no mock data
- [ ] GET /stakeholders/search FastAPI endpoint with query param filtering
- [ ] Both endpoints covered by unit tests with seeded data
- [ ] Milo daily briefing includes a Stakeholder Health block when any stakeholder has status=pending for >7 days
- [ ] Milo hourly monitor flags high-influence stakeholders with satisfaction <= 2 as a risk
- [ ] stakeholder__read and stakeholder__search respect tenant isolation (only return stakeholders for the authenticated tenant)
- [ ] End-to-end test: Milo calls stakeholder__read on a seeded program and returns correct stakeholder records
- [ ] End-to-end test: Milo calls stakeholder__search with role='sponsor' and returns correct filtered results
- [ ] No breaking changes to existing stakeholder__invite tool or work_item__update stakeholder entity type

## Technical Notes
- Stakeholders table already exists, linked to work items via parent_id. Schema includes: id, stakeholder_sub, role, influence, interest, satisfaction, status (pending/active/revoked), created_at.
- Add last_active_at column (nullable timestamp) to stakeholders table via Alembic migration — populated when stakeholder logs in via magic link.
- invited_at = created_at (alias in API response, no schema change needed).
- email field: stakeholder_sub currently stores the email address (per stakeholder__invite implementation) — expose as 'email' in API response.
- Tenant isolation: all queries must filter by tenant_id via the authenticated request context (same pattern as work_item__read).
- Register both tools in tools_config.py using the same Bedrock tool registration pattern as existing tools.
- FastAPI router: add stakeholders.py router to app/routers/ — GET /stakeholders and GET /stakeholders/search.
- Daily briefing Lambda: add stakeholder health block — query stakeholder__read for all programs, flag pending > 7 days.
- Hourly monitor Lambda: add high-influence low-satisfaction risk check using stakeholder__read.
- Do NOT modify stakeholder__invite or the existing work_item__update stakeholder path.
