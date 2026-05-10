# Milo UI Overhaul — Multi-Tenant Program Dashboard (All Personas) v2

**Date:** 2026-05-10T01:39:13.625340
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
This is a re-filing of the Milo UI overhaul spec. The original redesign (work item 32717bdf) was partially implemented — the navigation shell and right-rail chat were built, but the data layer, persona-aware defaults, and several core pages were never completed. This spec supersedes the original and must be treated as a full build requirement.

**Scope: 5 Pages**

1. **Home — Mission Control**
   - Health rings: On Track / At Risk / Off Track counts, wired to live RAG status API
   - Approvals badge on sidebar: real-time count from approval__read, updates on queue change
   - Upcoming milestones panel: next 7 days, sorted by due date
   - Milo activity feed: last 10 autonomous actions taken by Milo for this tenant
   - Quick Actions bar: New Task, Log Decision, Flag Risk, Ask Milo
   - Zero mocks — all panels must render a graceful empty state (not a spinner) when no data exists

2. **Program Detail — War Room**
   - 6 tabs: Overview, Work Items, Decisions, Risks, Stakeholders, Financials
   - 8-layer inline drill-down (Program → Initiative → Project → Milestone → Epic → Story → Task → Subtask), Linear-style, no page reload
   - Breadcrumb updates at every drill-down level
   - Critical path DAG with what-if simulation (drag to reschedule, see downstream impact)
   - RAG status auto-computed from child item rollup

3. **Portfolio View**
   - Health matrix across all programs
   - Resource heatmap: who is over-allocated across programs
   - Financials charts: budget vs. actuals per program

4. **Approvals Queue**
   - Inline approve/reject with comment
   - Mobile swipe gesture: swipe right = approve, swipe left = reject
   - Email fallback: if approver doesn't open UI, reply-to-email triggers approval__respond
   - Real-time badge count wired to approval__read

5. **Settings**
   - Persona-aware defaults: 6 roles (Executive, PM, Engineer, Finance, Product, Stakeholder) each get a different default Home layout and notification cadence
   - Tenant config, integrations, audit log — already partially built, verify completeness

**Stack:** Next.js 15, shadcn/ui, Tailwind v4, Framer Motion (transitions ≤ 300ms), Zustand, React Query. All data via live APIs — zero mocks anywhere in production paths.

**Extends work item:** 32717bdf

## Acceptance Criteria
- [ ] Home dashboard renders 4 live data panels (health rings, approvals badge, milestones, activity feed) — all wired to real APIs with no mock data
- [ ] Home dashboard renders a graceful, styled empty state for each panel when no data exists — no spinners left indefinitely
- [ ] Sidebar approvals badge shows real-time count from approval__read and updates immediately when queue changes
- [ ] Quick Actions bar (New Task, Log Decision, Flag Risk, Ask Milo) is present and functional on the Home page
- [ ] Program detail supports 8-layer inline drill-down (Program → Initiative → Project → Milestone → Epic → Story → Task → Subtask) with no page reload
- [ ] Breadcrumb updates correctly at every drill-down level
- [ ] Critical path DAG renders on Program Overview tab with what-if drag-to-reschedule simulation showing downstream impact
- [ ] RAG status is auto-computed from child item rollup — no manual override required
- [ ] Portfolio view includes resource heatmap (over-allocation flagged) and financials charts (budget vs. actuals per program)
- [ ] Approvals Queue supports inline approve/reject with comment, mobile swipe gestures (right = approve, left = reject), and email reply fallback via approval__respond
- [ ] Persona-aware defaults are applied on login: each of the 6 roles (Executive, PM, Engineer, Finance, Product, Stakeholder) gets a distinct default Home layout and notification cadence
- [ ] All Framer Motion transitions complete in ≤ 300ms
- [ ] Lighthouse accessibility score ≥ 90 on Home, Program Detail, and Approvals pages
- [ ] Zero mock data in any production code path — all data fetched via React Query from live API endpoints
- [ ] All 5 pages (Home, Program Detail, Portfolio, Approvals, Settings) pass a full QA pass against this spec before marking COMPLETED

## Technical Notes
This is a re-file. The original spec (PENDING_milo_ui_redesign.md in archive) was partially built — navigation shell, right-rail chat, and global search (cmd+K) are confirmed live and do NOT need to be rebuilt. Focus effort on: (1) Home data layer, (2) 8-layer drill-down, (3) critical path DAG, (4) persona-aware defaults, (5) approvals badge wiring, (6) mobile swipe on approvals, (7) resource heatmap + financials charts. The approval__read, approval__create, approval__respond, approval__cancel tools are now live in the MCP runtime — use them directly for all approvals UI data. Do not rename the archive file to COMPLETED_ until all 15 acceptance criteria above are verified by Scott.
