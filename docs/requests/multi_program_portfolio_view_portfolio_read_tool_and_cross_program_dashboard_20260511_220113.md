# Multi-Program Portfolio View — portfolio__read Tool and Cross-Program Dashboard

**Date:** 2026-05-11T22:01:13.589733
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently operates on individual programs in isolation. There is no capability to view, compare, or reason across multiple programs simultaneously. This capability adds a Portfolio View — a cross-program dashboard that aggregates health status (RAG), milestone progress, resource allocation, financial variance, and risk exposure across all active programs for a tenant. Milo should be able to call a `portfolio__read` tool to get a structured summary of all programs, enabling portfolio-level briefings, risk roll-ups, and executive reporting. This is a P3 gap in the Milo 20-capability target list.

## Acceptance Criteria
- [ ] portfolio__read tool registered in Bedrock payload and callable by Milo
- [ ] Returns list of all active programs with health (RAG), milestone_count, overdue_task_count, open_risk_count, budget_variance_pct
- [ ] Health (RAG) computed server-side: RED = any overdue milestone or critical unresolved risk; YELLOW = overdue tasks or budget variance > 10%; GREEN = all clear
- [ ] portfolio__read accepts optional filters: status (active | planned | complete), owner_name
- [ ] GET /portfolio FastAPI endpoint covered by unit tests
- [ ] Milo daily briefing includes a portfolio summary block when 2+ active programs exist
- [ ] UI: Portfolio page renders program grid/heatmap with RAG indicators, milestone progress bars, risk badges
- [ ] UI: Clicking a program card navigates to Program Detail page
- [ ] UI: Resource heatmap shows owner workload across all programs
- [ ] UI: Financials chart shows budget vs. actual per program (if data present)
- [ ] Lighthouse accessibility >= 90 on Portfolio page
- [ ] Zero mock data in any production code path
- [ ] End-to-end test: Milo calls portfolio__read with 2+ seeded programs and returns correct aggregated health

## Technical Notes
Aggregate across all work items of type 'objective', 'initiative', or 'project' for the tenant. Expose as GET /portfolio FastAPI endpoint. Register portfolio__read as a Bedrock tool in tools_config.py. Frontend: Portfolio page shell already exists in Milo UI Redesign (work item 32717bdf) — wire to live API. Resource heatmap: group tasks by owner_name, count per program. Stack: Next.js 15, shadcn/ui, Tailwind v4, Framer Motion. Priority: P3.
