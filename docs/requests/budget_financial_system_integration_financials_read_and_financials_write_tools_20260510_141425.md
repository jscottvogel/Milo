# Budget & Financial System Integration — financials__read and financials__write Tools

**Date:** 2026-05-10T14:14:25.511951
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently has no live financial data access. Work items support a `metadata_json.financials` field (array of `{period, budget, actual}` objects), but there is no tool to query, aggregate, or surface this data autonomously. This capability adds two new Bedrock-registered tools — `financials__read` and `financials__write` — backed by FastAPI endpoints that read/write the JSONB financials field on work items, aggregate budget vs. actual across program hierarchies, and compute variance metrics. Milo will use these tools in daily briefings, risk assessments, and autonomous program health checks.

## Acceptance Criteria
- [ ] financials__read returns aggregated total_budget, total_actual, variance, variance_pct, and status (under_budget | over_budget | on_track) for a given program_id
- [ ] financials__read returns a by_period breakdown array [{period, budget, actual, variance}]
- [ ] financials__read returns a by_work_item breakdown array [{work_item_id, name, budget, actual}]
- [ ] financials__read accepts optional filters: program_id, work_item_id, period_start (YYYY-MM), period_end (YYYY-MM)
- [ ] financials__write upserts a {period, budget, actual} record into metadata_json.financials for a given work_item_id
- [ ] Both tools are registered in the Bedrock tool payload via tools_config.py and callable by Milo in the agent loop
- [ ] Aggregation uses recursive CTE or app-level rollup across all children of a program_id
- [ ] Variance % and status computed server-side — not in the agent
- [ ] Milo's daily briefing Lambda includes a financial summary block when financials data is present for any active program
- [ ] GET /financials and POST /financials FastAPI endpoints exist and are covered by unit tests
- [ ] End-to-end test: Milo calls financials__read on a seeded program and returns correct aggregated values
- [ ] No mock data in any production code path

## Technical Notes
Backend: Query `metadata_json->>'financials'` from `work_items` table using Postgres JSONB operators. Aggregate across all children of a program_id using recursive CTE or app-level rollup. Expose as two new FastAPI endpoints: GET /financials?program_id=&work_item_id=&period_start=&period_end= and POST /financials (upsert actuals). Register both as Bedrock tools in tools_config.py using the same pattern as work_item__read. Tool names: financials__read and financials__write. Frontend (Phase 2, optional): Budget vs. Actual sparkline on program dashboard, RAG status indicator (green/yellow/red) based on variance %. Priority: P2 — High.
