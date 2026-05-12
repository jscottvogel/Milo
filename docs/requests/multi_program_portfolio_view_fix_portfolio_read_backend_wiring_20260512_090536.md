# Multi-Program Portfolio View — Fix portfolio__read Backend Wiring

**Date:** 2026-05-12T09:05:36.387242
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
The `portfolio__read` tool is registered in the Bedrock tool payload but returns "Tool portfolio.read not found" when called by Milo. This was confirmed broken on 2026-05-14 during a full capability sweep. The tool was originally spec'd and handed off on 2026-05-10 but has not been wired to a live backend endpoint.

**What is needed:**
Milo needs a fully functional `portfolio__read` tool that returns an aggregated cross-program health view for the tenant. This enables portfolio-level briefings, RAG health roll-ups, and executive reporting across all active programs.

**Tool Signature:**
```
portfolio__read(
  status: "active" | "planned" | "complete" | null,
  owner_name: string | null
)
```

**Returns per program:**
- program_id, name, status
- health: RED | YELLOW | GREEN (computed server-side)
- milestone_count (int)
- overdue_task_count (int)
- open_risk_count (int)
- budget_variance_pct (float | null — only if financials data present)

**RAG Health Computation:**
- RED = any overdue milestone OR any critical unresolved risk (likelihood >= 4 AND impact >= 4)
- YELLOW = any overdue task OR budget_variance_pct > 10%
- GREEN = all clear

**Backend:**
- FastAPI endpoint: GET /portfolio
- Query all work items of type 'objective', 'initiative', or 'project' for the authenticated tenant
- Aggregate children recursively to compute milestone_count, overdue_task_count, open_risk_count
- Register as Bedrock tool in tools_config.py using the same pattern as work_item__read
- Tenant isolation: all queries filter by tenant_id from authenticated request context

**Root Cause of Current Failure:**
The tool is in the Bedrock payload schema but the FastAPI route and/or Bedrock tool registration is missing or misnamed. The tool name in the payload must exactly match the handler key — confirm it is `portfolio__read` (double underscore), not `portfolio.read`.

## Acceptance Criteria
- [ ] portfolio__read tool callable by Milo with no 'Tool not found' error
- [ ] Returns list of all programs for the tenant filtered by optional status and owner_name params
- [ ] Each program record includes: program_id, name, status, health (RED/YELLOW/GREEN), milestone_count, overdue_task_count, open_risk_count, budget_variance_pct
- [ ] RAG health computed server-side: RED=overdue milestone or critical risk, YELLOW=overdue task or budget variance >10%, GREEN=all clear
- [ ] GET /portfolio FastAPI endpoint live and returning correct data
- [ ] Tool registered in Bedrock payload with correct double-underscore naming convention (portfolio__read)
- [ ] Tenant isolation enforced — queries scoped to authenticated tenant_id
- [ ] Unit tests cover: empty portfolio, single program GREEN, single program RED, single program YELLOW, filter by status, filter by owner_name
- [ ] End-to-end test: Milo calls portfolio__read on seeded tenant with 2+ programs and returns correct aggregated health
- [ ] No mock data in any production code path
- [ ] Milo daily briefing includes portfolio summary block when 2+ active programs exist

## Technical Notes
CRITICAL: The tool is currently returning 'Tool portfolio.read not found' — this is a naming/registration bug. Confirm the Bedrock tool handler key uses double underscores (portfolio__read), not dot notation. Check tools_config.py and the Lambda tool dispatch table. The FastAPI route may also be missing entirely — check app/routers/ for a portfolio.py file. If absent, create it. Stack: FastAPI + SQLAlchemy + PostgreSQL JSONB. Aggregate using recursive CTE or app-level rollup across work item hierarchy. Do NOT modify the daily briefing Lambda — only add the new endpoint and tool registration.
