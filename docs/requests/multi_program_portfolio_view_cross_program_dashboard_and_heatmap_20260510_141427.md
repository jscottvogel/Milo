# Multi-Program Portfolio View — Cross-Program Dashboard and Heatmap

**Date:** 2026-05-10T14:14:27.822843
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently operates on individual programs in isolation. There is no capability to view, compare, or reason across multiple programs simultaneously. This capability adds a Portfolio View — a cross-program dashboard that aggregates health status, milestone progress, resource allocation, financial variance, and risk exposure across all active programs for a tenant. Milo should be able to call a `portfolio__read` tool to get a structured summary of all programs, enabling portfolio-level briefings, risk roll-ups, and executive reporting.

## Acceptance Criteria
- [ ] portfolio__read tool is registered in the Bedrock payload and callable by Milo
- [ ] portfolio__read returns a list of all active programs for the tenant with: program_id, name, status, health (RAG), milestone_count, overdue_task_count, open_risk_count, budget_variance_pct (if financials present)
- [ ] Health (RAG) is computed server-side from: overdue tasks, unresolved risks, stalled milestones, and budget variance
- [ ] portfolio__read accepts optional filters: status (active | planned | complete), owner_name
- [ ] GET /portfolio FastAPI endpoint exists and is covered by unit tests
- [ ] Milo's daily briefing includes a portfolio summary block when 2+ active programs exist
- [ ] UI: Portfolio page renders a program grid/heatmap with RAG indicators, milestone progress bars, and risk badges
- [ ] UI: Clicking a program card navigates to the Program Detail page
- [ ] UI: Resource heatmap shows owner workload across all programs (tasks assigned per owner)
- [ ] UI: Financials chart shows budget vs. actual per program (if data present)
- [ ] Lighthouse accessibility >= 90 on Portfolio page
- [ ] Zero mock data in any production code path
- [ ] End-to-end test: Milo calls portfolio__read with 2+ seeded programs and returns correct aggregated health

## Technical Notes
Backend: Aggregate across all work items of type 'objective', 'initiative', or 'project' for the tenant. RAG computation: RED = any overdue milestone or critical unresolved risk; YELLOW = overdue tasks or budget variance > 10%; GREEN = all clear. Expose as GET /portfolio FastAPI endpoint. Register portfolio__read as a Bedrock tool in tools_config.py. Frontend: Next.js 15, shadcn/ui, Tailwind v4, Framer Motion. Portfolio page already exists as a shell in the Milo UI Redesign work item (32717bdf) — wire it to the live API. Resource heatmap: group tasks by owner_name, count per program. Priority: P3.
