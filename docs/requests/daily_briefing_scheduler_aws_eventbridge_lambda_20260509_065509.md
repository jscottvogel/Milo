# Daily Briefing Scheduler — AWS EventBridge + Lambda

**Date:** 2026-05-09T06:55:09.888751
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Every morning at a configured time (default 7:00 AM tenant local time), Milo must automatically compose and send a structured daily briefing to the tenant's primary email address. The job reads unread emails, calendar events for today and the next 7 days, open work items (risks, overdue tasks, upcoming milestones), evaluates all trigger rules, composes a structured briefing, and sends it via Nylas email. The briefing is also written to episodic memory after send. This makes Milo fully autonomous in the morning without requiring a human prompt.

## Acceptance Criteria
- [ ] AWS EventBridge Scheduler triggers the briefing Lambda on a per-tenant cron schedule respecting tenant timezone
- [ ] AWS Lambda handler executes the full Milo briefing job: read emails, read calendar, read work items, evaluate triggers, compose briefing, send email
- [ ] IAM Role for Lambda is least-privilege — only the permissions it needs
- [ ] Briefing email matches the defined format: Inbox summary, Today, This Week, Risks & Blockers, Pending Approvals, Upcoming Milestones
- [ ] Tenant can configure send time and toggle the briefing on/off in Settings → Persona
- [ ] Timezone is pulled from tenant profile and applied correctly to EventBridge schedule
- [ ] Lambda is idempotent — safe to retry on failure without duplicate sends
- [ ] Briefing is written to episodic memory (kind: event) after successful send
- [ ] No Vercel Cron or pg_cron — EventBridge is the sole scheduler

## Technical Notes
Deployment is AWS. Use EventBridge Scheduler (not EventBridge Events) for per-tenant cron expressions. Lambda should read tenant config (send time, timezone, recipient, toggle) from the database at invocation time. Reuses existing Milo tool chain — no new integrations needed. Flow: EventBridge Scheduler → Lambda → Milo briefing job → Nylas email send.
