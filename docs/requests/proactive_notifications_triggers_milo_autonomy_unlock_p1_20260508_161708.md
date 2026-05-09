# Proactive Notifications & Triggers — Milo Autonomy Unlock (P1)

**Date:** 2026-05-08T16:17:08.169922
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Build a scheduler and trigger engine that allows Milo to run autonomously on a cadence and react to events without human initiation. Currently, Milo ONLY acts when a human speaks to it. This is the #1 critical capability gap.

## SYSTEM CONTEXT

Milo is a Python-based agentic AI coordinator built on the Nylas platform. The following tools are already live: email__read, email__send, calendar__read, calendar__write, memory__search, memory__write, work_item__read, work_item__update, storage__read, storage__write, web__search, web__fetch, document__generate, file__read, meeting__attend, handoff__human, developer__handoff.

## THREE COMPONENTS REQUIRED

### COMPONENT 1 — Scheduler (Cron Runner)
A lightweight scheduler that invokes Milo's morning briefing routine automatically every day at a configurable time (default: 7:00 AM tenant local time).

The morning briefing routine must:
1. Call email__read to check for unread emails
2. Call calendar__read for today's and tomorrow's events
3. Call work_item__read to surface overdue tasks and upcoming milestones
4. Call memory__search for any pending action items or flagged risks
5. Compose a structured daily briefing and send it via email__send to the tenant owner (j_scott_vogel@yahoo.com)
6. Write a memory entry confirming the briefing was sent

### COMPONENT 2 — Trigger Rules Engine
A configurable rules engine that evaluates conditions and fires Milo actions when thresholds are met. Four built-in rules:

RULE 1 — Unread Email Escalation
  Condition: An email from a known stakeholder has been unread for > 24 hours
  Action: Milo drafts a summary and sends an alert to the tenant owner

RULE 2 — Overdue Task Alert
  Condition: A work item task has a due_date in the past and status != complete
  Action: Milo sends an email alert listing all overdue items with owners

RULE 3 — Upcoming Milestone Warning
  Condition: A milestone is due within 7 days and status != complete
  Action: Milo sends a milestone warning email to the tenant owner

RULE 4 — Stale Program Warning
  Condition: No work item has been updated in > 7 days
  Action: Milo sends a program health check nudge to the tenant owner

### COMPONENT 3 — Push Notification Channel
A mechanism for Milo to reach the tenant owner without being prompted. For v1, email-based (email__send to j_scott_vogel@yahoo.com). Design the interface so SMS or Slack can be swapped in later.

## NEW TOOL TO ADD

`trigger__evaluate`
  Description: Evaluate all configured trigger rules and fire any actions whose conditions are met.
  Parameters: None required. Optionally accepts { rule_id: string } to run a single rule.
  Returns: List of rules evaluated, conditions met, and actions taken.

## TECHNICAL CONSTRAINTS

1. Budget: < $100/month total operational cost
2. Scheduler: Use APScheduler, cron, or cloud-native scheduler — no heavy orchestration frameworks
3. Auth: OAuth2 only — no credentials in logs, memory, or storage
4. Idempotency: Use memory__search before firing any alert to check if already sent today
5. Error handling: If any tool call fails during a scheduled run, log to memory and continue — do not crash
6. Tenant isolation: All reads and writes strictly scoped to current tenant
7. Structured output: All trigger results must be JSON-serializable
8. Future-proofing: Design trigger rules as data (JSON/YAML config), not hardcoded logic

## Acceptance Criteria
- [ ] Milo sends a morning briefing email to j_scott_vogel@yahoo.com every day at 7:00 AM without any human prompt
- [ ] The morning briefing includes: unread email count, today's calendar events, overdue tasks, upcoming milestones (next 7 days), and any flagged risks
- [ ] trigger__evaluate runs all 4 built-in rules and returns structured results
- [ ] Overdue task alert fires correctly when a task is past due_date
- [ ] Milestone warning fires correctly when a milestone is within 7 days
- [ ] Unread email escalation fires after 24h threshold is breached
- [ ] Stale program warning fires after 7 days of no updates
- [ ] All trigger actions are logged to memory via memory__write
- [ ] Scheduler is configurable — time of day changeable without code changes (env var or config file)
- [ ] Push channel is abstracted — v1 uses email, interface supports future SMS/Slack swap-in
- [ ] No trigger fires more than once per evaluation window (idempotency — no duplicate alerts)
- [ ] All existing tools remain fully functional — no regressions
- [ ] End-to-end test: disable morning briefing for 1 day, re-enable, confirm it fires and email is received

## Technical Notes
Trigger rules should be stored as JSON/YAML config so new rules can be added without code changes. Use memory__search with a dated key (e.g. 'trigger_fired_RULE1_2025-01-15') to enforce idempotency. The push notification channel should be an abstracted interface (e.g. notify(channel, message)) with an EmailChannel implementation in v1. APScheduler with a persistent job store is recommended to survive restarts. All scheduled run results — including errors — must be written to memory for auditability.
