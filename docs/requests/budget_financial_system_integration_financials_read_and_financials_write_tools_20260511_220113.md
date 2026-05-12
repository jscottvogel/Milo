# Budget & Financial System Integration — financials__read and financials__write Tools

**Date:** 2026-05-11T22:01:13.568727
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently has no live financial data access. Work items support a `metadata_json.financials` field (array of `{period, budget, actual}` objects), but there is no tool to query, aggregate, or surface this data autonomously. This capability adds two new Bedrock-registered tools — `financials__read` and `financials__write` — backed by FastAPI endpoints that read/write the JSONB financials field on work items, aggregate budget vs. actual across program hierarchies, and compute variance metrics. This is a P2 (High Priority) gap in the Milo 20-capability target list.

## Acceptance Criteria
- [ ] financials__read tool registered in Bedrock payload and callable by Milo
- [ ] financials__read returns aggregated total_budget, total_actual, variance, variance_pct, and status (under_budget | over_budget | on_track) for a given program_id
- [ ] financials__read returns a by_period breakdown array [{period, budget, actual, variance}]
- [ ] financials__read returns a by_work_item breakdown array [{work_item_id, name, budget, actual}]
- [ ] financials__read accepts optional filters: program_id, work_item_id, period_start (YYYY-MM), period_end (YYYY-MM)
- [ ] financials__write tool registered in Bedrock payload and callable by Milo
- [ ] financials__write upserts a {period, budget, actual} record into metadata_json.financials on the specified work item
- [ ] Aggregation uses recursive CTE or app-level rollup across all children of a program_id
- [ ] Variance % and status computed server-side
- [ ] GET /financials and POST /financials FastAPI endpoints covered by unit tests
- [ ] Milo daily briefing includes a financial summary block when financials data is present
- [ ] End-to-end test: Milo calls financials__read on a seeded program and returns correct aggregated values
- [ ] No mock data in any production code path
- [ ] Both tools respect tenant isolation

## Technical Notes
Query metadata_json->>'financials' from work_items table using Postgres JSONB operators. Aggregate across all children of a program_id using recursive CTE or app-level rollup. Expose as GET /financials and POST /financials FastAPI endpoints. Register both as Bedrock tools in tools_config.py (same pattern as work_item__read). Variance % and status computed server-side. Daily briefing Lambda includes financial summary block when data is present. Priority: P2.
