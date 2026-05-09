# Milo UI Overhaul — Multi-Tenant Program Dashboard for All Personas

**Date:** 2026-05-09T14:50:55.112724
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description

## Overview

The current Milo UI is functional but not usable at scale. This spec defines a complete UI overhaul that makes every program's status, health, risks, financials, and critical path immediately legible to any persona — executive, program manager, stakeholder, engineer, product manager, or finance lead — without requiring them to dig through raw data or ask Milo a question.

All data must be wired to live API endpoints. Zero mocks. Zero hardcoded values.

---

## Core Design Principles

1. **Persona-aware information density.** The same screen should surface the right signal for each role. Executives see RAG status and financials. Engineers see tasks and blockers. Finance sees burn vs. budget. PMs see critical path and risks.
2. **No dead ends.** Every number, status badge, and chart is clickable and drills into the underlying data.
3. **Milo is always present.** The AI chat rail is persistent and context-aware — it knows what you're looking at and can answer questions about it.
4. **Real data only.** Every widget pulls from the live work_item, risk, decision, financials, and critical_path APIs. No static fixtures.
5. **Multi-tenant safe.** Tenant isolation is enforced at the API layer (RLS). The UI must never leak cross-tenant data. Tenant switcher (for admin/super-admin roles) must be clearly scoped.

---

## Page 1: Home Dashboard ("Mission Control")

The first screen a user sees after login. Designed for a 30-second executive briefing.

### Layout: 3-column grid

**Column 1 — Portfolio Health Strip**
- One card per active program under management
- Each card shows:
  - Program name
  - RAG status indicator (Red / Amber / Green) — computed from: overdue milestones, open P1 risks, budget variance >10%
  - % complete (milestone-based)
  - Days to next milestone
  - Owner name
  - One-line Milo-generated status summary (pulled from latest briefing or generated on load)
- Clicking a card navigates to the Program Detail page

**Column 2 — Attention Required**
- Unified feed of items needing human action, sorted by urgency:
  - Pending approvals (badge count)
  - Overdue tasks (owner + days late)
  - Unread emails flagged by Milo as requiring response
  - Open risks with no mitigation assigned
  - Decisions with no decision_text recorded
- Each item is actionable inline (approve/reject, mark resolved, open thread)

**Column 3 — Milo Chat Rail**
- Persistent across all pages
- Context-aware: knows which program/page is active
- Supports natural language queries: "What's blocking Phase 5?", "Show me all P1 risks", "Draft a status update for the sponsor"
- Shows last 5 Milo actions taken (with timestamps)

**Top Bar**
- Tenant name + logo (pulled from tenant profile)
- User avatar + role badge
- Global search (searches across all programs, tasks, risks, decisions, emails)
- Notification bell (approval requests, overdue alerts, Milo nudges)

---

## Page 2: Program Detail ("The War Room")

Accessed by clicking any program card. This is the primary working surface.

### Sub-navigation tabs:

**Tab 1: Overview**
- Program name, description, owner, status badge, start/due dates
- Key Results panel: each KR with status pill (not_started / in_progress / complete) and progress bar
- Milestone timeline: horizontal swimlane showing all milestones, color-coded by status, with today marker
- Critical Path panel:
  - Rendered as a horizontal DAG (nodes = milestones/tasks, edges = dependencies)
  - Zero-float nodes highlighted in red
  - Hover tooltip: task name, owner, duration, float
  - "What-if" slider: drag a node to simulate a slip and see downstream impact in real time
- Milo Summary card: AI-generated paragraph summarizing program health, top risk, and recommended next action

**Tab 2: Work Breakdown**
- Full 8-layer hierarchy rendered as an expandable tree (Objective → Outcome → KR → Initiative → Project → Workstream → Milestone → Task)
- Each row shows: name, owner, status pill, due date, % complete
- Inline status editing (click status pill to change)
- Filter bar: by status, owner, due date range, layer type
- Bulk actions: reassign owner, change status, export to CSV

**Tab 3: Risks & Decisions**
- **Risks table**: title, likelihood (1–5), impact (1–5), computed severity score (L×I), status, mitigation, owner
  - Color-coded severity: green (1–4), amber (5–9), red (10–25)
  - Inline mitigation editing
  - "Add Risk" button → modal form
- **Decisions log**: title, decision_text, alternatives considered, date recorded, source link
  - Filterable by date range
  - "Add Decision" button → modal form
- **Change Requests**: title, description, reason, impact analysis, status (pending/approved/rejected)

**Tab 4: Financials**
- Budget vs. Actual chart (bar chart, monthly periods)
- Burn rate trend line
- Variance table: period, budget, actual, variance ($), variance (%)
- Forecast to completion (linear extrapolation from current burn rate)
- All data sourced from work item `metadata_json.financials` array
- Export to CSV button

**Tab 5: Stakeholders**
- Stakeholder grid: name, role, email, influence (H/M/L), interest (H/M/L), satisfaction score, notes
- Influence/Interest matrix (2×2 quadrant chart, plotted from live data)
- "Add Stakeholder" button
- Click row → stakeholder detail panel with full notes and action items

**Tab 6: Inbox (Program-scoped)**
- Emails and meeting notes related to this program (filtered by program name / stakeholder emails)
- Unread badge count
- Click email → full thread view with Milo's suggested reply pre-drafted

---

## Page 3: Portfolio View (Multi-Program)

For users managing 2+ programs. Designed for PMO leads and executives.

### Layout:

**Portfolio Health Matrix**
- Grid of all programs: rows = programs, columns = key health dimensions
- Columns: Overall RAG | Schedule | Budget | Risk | Stakeholder Satisfaction | % Complete | Days to Next Milestone
- Color-coded cells (red/amber/green per dimension)
- Sortable by any column
- Click row → Program Detail

**Gantt-style Timeline**
- All programs on a single horizontal timeline
- Milestones shown as diamonds, phases as bars
- Color by RAG status
- Zoom: week / month / quarter
- Today line

**Cross-Program Risk Register**
- All open risks across all programs in one table
- Filterable by program, severity, status
- Sortable by severity score

**Resource Heatmap**
- Owner names on Y-axis, weeks on X-axis
- Cell color = task load (green = available, amber = loaded, red = overloaded)
- Sourced from task assignments and due dates

---

## Page 4: Approvals Queue

First-class page, not buried in settings.

- List of all pending approval requests
- Each row: request title, program, requestor, date submitted, urgency, approve/reject buttons
- Approved/rejected history with timestamps and actor
- Email notification sent on approval/rejection (via existing Nylas integration)

---

## Page 5: Settings & Tenant Configuration

- Tenant profile: name, logo, timezone, daily briefing time (on/off toggle + time picker)
- User management: invite users, assign roles (Executive / PM / Engineer / Finance / Stakeholder / Admin)
- Integrations: connection status for Nylas email, Nylas calendar, Stripe, GitHub, DocuSign, HubSpot
- Data retention policy selector
- Audit log export (date range → CSV)

---

## Role-Based View Defaults

When a user logs in, their role determines the default tab and information density:

| Role | Default Landing | Key Widgets Surfaced |
|---|---|---|
| Executive | Home Dashboard | RAG strip, KPIs, Milo summary |
| Program Manager | Program Detail → Overview | Critical path, milestones, risks |
| Engineer | Program Detail → Work Breakdown | Tasks assigned to me, blockers |
| Finance | Program Detail → Financials | Budget vs actual, burn rate |
| Product Manager | Program Detail → Work Breakdown | KRs, initiatives, milestone status |
| Stakeholder | Home Dashboard (read-only) | RAG strip, milestone timeline |

---

## API Wiring Requirements

Every UI component must call a real endpoint. No mocks permitted in production builds.

| UI Component | API / Tool |
|---|---|
| RAG status | Computed from work_item__read + risk data |
| Critical path DAG | program__critical_path |
| Work breakdown tree | work_item__read (include_children=true) |
| Financials charts | work_item metadata_json.financials |
| Risk table | work_item__read risks[] |
| Stakeholder matrix | work_item__read stakeholders[] |
| Approvals queue | approval__read (from approval workflow engine) |
| Inbox | email__read (filtered by program context) |
| Milo chat rail | Agent API (existing LangGraph endpoint) |
| Daily briefing toggle | Tenant settings API |
| Audit log | Audit log export API |


## Acceptance Criteria
- [ ] Home Dashboard loads within 2 seconds and displays RAG status, % complete, and days-to-next-milestone for every active program — sourced from live API, zero mocks.
- [ ] RAG status is computed server-side from: overdue milestones, open P1/P2 risks with no mitigation, and budget variance >10%. Logic is documented and testable.
- [ ] Critical path DAG renders correctly for any program with dependencies defined. Zero-float nodes are highlighted red. Hover tooltip shows task name, owner, duration, and float.
- [ ] What-if slip simulation: dragging a node on the DAG re-calls program__critical_path with what_if parameters and re-renders downstream impact within 1 second.
- [ ] Work breakdown tree supports full 8-layer hierarchy (Objective → Task). Expand/collapse works at every level. Inline status editing persists to the database.
- [ ] Financials tab renders budget vs. actual bar chart and burn rate trend line from work item metadata_json.financials. Export to CSV works.
- [ ] Stakeholder influence/interest matrix is plotted from live stakeholder data. Quadrant positions update when stakeholder influence/interest values change.
- [ ] Approvals queue is a first-class page with badge count in the nav. Approve/reject actions call the approval API and send email notification via Nylas.
- [ ] Role-based default views are enforced at login. Executive lands on Home Dashboard. Engineer lands on Work Breakdown filtered to their assigned tasks.
- [ ] Tenant switcher (admin only) is clearly scoped and never leaks cross-tenant data. All API calls include tenant_id from Cognito JWT.
- [ ] Milo chat rail is persistent across all pages and is context-aware (knows active program/page). It can answer questions about the currently viewed program.
- [ ] Portfolio view renders a health matrix for all programs with sortable columns (RAG, schedule, budget, risk, % complete). Clicking a row navigates to Program Detail.
- [ ] All pages are responsive down to 1280px width minimum. No horizontal scroll on standard laptop screens.
- [ ] Global search returns results across programs, tasks, risks, decisions, and emails within 1 second.
- [ ] All data-fetching components show a loading skeleton (not a spinner) while awaiting API response, and a graceful error state if the API fails.

## Technical Notes

Stack: Next.js 15 (App Router), shadcn/ui, Tailwind v4, Framer Motion (transitions), Zustand (client state), React Query (server state + caching).

Critical path DAG: Use a lightweight graph layout library (e.g. dagre or elkjs) to compute node positions. Render with SVG or React Flow. Do NOT use a full Gantt library — keep it custom and fast.

RAG computation: Build a server-side utility function `compute_rag(program_id)` that returns { overall, schedule, budget, risk } with values 'red' | 'amber' | 'green'. Cache result in Redis with 5-minute TTL. Invalidate on any work item update for that program.

Financials: The financials array in metadata_json follows the schema: [{ "period": "YYYY-MM", "budget": number, "actual": number }]. Chart library: Recharts (already likely in stack) or Tremor.

Role-based views: Roles are stored as a custom Cognito attribute. Read role from JWT on login and set Zustand store. Use a `useRole()` hook to gate component visibility.

Multi-tenant: Never pass tenant_id from the client. Always derive it server-side from the verified Cognito JWT. The API already enforces RLS — the UI just needs to not expose tenant_id in URLs or local storage.

Milo chat rail: Wire to the existing `/api/agent/chat` endpoint. Pass `{ program_id, page_context }` as system context with every message. Stream the response using SSE or Vercel AI SDK `useChat`.

Approvals queue: Depends on the Approval Workflow Engine (engineering_requests/approval_workflow_engine.md) being live. If not yet live, render the queue as empty with a "No pending approvals" state — do not mock data.

Performance: Use React Query's `staleTime: 60_000` for work item data. Use `suspense: true` + Suspense boundaries for skeleton loading states. Prefetch Program Detail data on hover of portfolio cards.

Existing work item: This spec extends the existing 'Milo UI Redesign' project (ID: 32717bdf-3f4e-4897-986f-ad4fbf24ad8d). All tasks should be created as children of that project.

