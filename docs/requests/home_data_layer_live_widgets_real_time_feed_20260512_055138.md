# Home Data Layer — Live Widgets & Real-Time Feed

**Date:** 2026-05-12T05:51:38.748706
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
The Milo Home screen is currently displaying mocked or empty data. This handoff covers wiring all Home screen widgets to live backend data so every user sees an accurate, real-time view of their program portfolio on every login.

**Widgets to wire up:**

1. **Health Rings** — Pull from `portfolio__read` (or work_item__read aggregation). Display RAG status per active program as colored rings. Red = 1+ overdue milestones or unresolved P1 risks. Amber = 1+ stalled tasks or unresolved P2 risks. Green = all clear.

2. **Approvals Badge** — Pull from `approval__read` (all pending). Display count badge on the Approvals nav item and as a prominent card on Home. Badge should update in real-time (WebSocket or polling every 60s).

3. **Milestones Panel** — Pull from `work_item__read` across all active programs. Show next 5 upcoming milestones (sorted by due_date ASC) and any overdue milestones. Each row: program name, milestone name, due date, RAG chip, owner.

4. **Activity Feed** — Pull from episodic memory (`memory__search`) and work item update history. Show last 10 events across all programs: task completions, risk escalations, approvals decided, handoffs filed. Each row: timestamp, event type icon, description, linked program.

5. **Quick Actions Bar** — Persistent bar at top of Home with 4 actions: (a) New Approval Request, (b) Log a Risk, (c) Add a Task, (d) Invite Stakeholder. Each opens a modal pre-wired to the relevant tool (`approval__create`, `work_item__update`, `stakeholder__invite`).

**Data refresh strategy:**
- Health rings + milestones panel: refresh on page load + every 5 minutes
- Approvals badge: WebSocket preferred; polling fallback every 60s
- Activity feed: refresh on page load + every 2 minutes
- Quick actions: static (no refresh needed)

**Empty states:** Every widget must have a well-designed empty state (not a blank panel). E.g., "No upcoming milestones — you're on track!" with a subtle illustration.

## Acceptance Criteria
- [ ] Health rings render with correct RAG color for each active program based on live portfolio__read or work_item__read data — no mocked values
- [ ] Approvals badge displays accurate count of pending approvals from approval__read and updates within 60 seconds of a new approval being created
- [ ] Milestones panel shows next 5 upcoming milestones and all overdue milestones, sorted by due_date, with program name, owner, and RAG chip
- [ ] Activity feed displays last 10 real events from memory and work item history with correct timestamps, icons, and program links
- [ ] Quick Actions bar is visible on Home with all 4 actions (New Approval, Log Risk, Add Task, Invite Stakeholder) opening functional modals
- [ ] All modals in Quick Actions bar are pre-wired to the correct backend tools and submit successfully
- [ ] All widgets display a designed empty state when no data is available — no blank panels
- [ ] Health rings, milestones panel, and activity feed auto-refresh without full page reload
- [ ] Approvals badge reflects real-time count via WebSocket or polling fallback (≤60s lag)
- [ ] Home screen loads fully in under 2 seconds on a standard broadband connection
- [ ] All widgets are responsive and render correctly on mobile (375px) and desktop (1440px)
- [ ] No hardcoded or mocked data remains in any Home screen component after this build

## Technical Notes
portfolio__read, approval__read, work_item__read, memory__search, approval__create, work_item__update, and stakeholder__invite are all confirmed live tools. Use these as the data sources. Do not mock any data. For the activity feed, combine memory__search results (query: recent events) with work item update timestamps. WebSocket endpoint for approvals badge should reuse any existing WS infrastructure; if none exists, implement 60s polling as fallback. Quick Actions modals should reuse existing form components where possible. RAG computation logic: Red = overdue milestone OR unresolved risk with impact>=4. Amber = stalled task (no update in 7+ days) OR unresolved risk impact 2-3. Green = none of the above.
