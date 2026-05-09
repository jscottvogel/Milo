# Milo Autonomous Wake-Up Scheduler — EventBridge + LangGraph Trigger Engine

**Date:** 2026-05-09T12:22:10.405237
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently only executes when a user sends a message. To achieve true autonomy, Milo needs a scheduled execution engine that wakes her up on a cadence and on external events — without any human prompt.

This handoff covers four trigger types:

1. **Daily 7AM Morning Briefing** — A cron-based trigger that invokes the Milo LangGraph agent every morning at 7AM in the tenant's local timezone. Milo should read the inbox, scan the calendar, check work item statuses, evaluate trigger rules, and email a morning briefing to j_scott_vogel@yahoo.com.

2. **Email Webhook Trigger** — When a new email arrives in the connected inbox, fire a webhook that invokes the Milo LangGraph graph. Milo should triage the email, determine if action is needed, and either act autonomously or escalate to the human via the approval queue.

3. **Hourly Health Check Cron** — Every hour, invoke a lightweight Milo graph run that evaluates all trigger rules (trigger__evaluate), checks for overdue tasks, unread escalations, and stale programs. If any rule fires, Milo takes action and writes to memory.

4. **Stale Program Daily Scan** — Once per day (can be combined with morning briefing), scan all active programs for items with no updates in 7+ days and surface them in the briefing or send a nudge email.

All triggers must invoke the full LangGraph agent loop (agent → tools → agent → END) with the correct system prompt and tenant context loaded. Each run must write a memory entry on completion so Milo knows what she did and when.

## Acceptance Criteria
- [ ] Daily 7AM cron fires reliably in tenant local timezone (America/Chicago default) using AWS EventBridge or equivalent scheduler
- [ ] Morning briefing run reads inbox, calendar, work items, and trigger rules in a single autonomous graph execution
- [ ] Morning briefing email is sent to j_scott_vogel@yahoo.com with structured summary of: unread emails, today's calendar, overdue tasks, active risks, and any fired trigger rules
- [ ] Email webhook triggers a Milo graph run within 60 seconds of new email receipt
- [ ] Hourly health check cron invokes trigger__evaluate and acts on any rules that fire
- [ ] Each autonomous run writes a memory entry with kind='event', recording what was done, what fired, and timestamp
- [ ] No duplicate actions — each run checks memory to confirm the same action was not already taken in the last 24 hours (idempotency via memory__search)
- [ ] If a graph run exceeds 10 minutes or 50 tool calls, it self-terminates and writes a stall memory entry, then emails the user
- [ ] All triggers load the correct tenant context and system prompt before invoking the agent
- [ ] A daily run summary is written to storage at logs/daily_run_YYYY-MM-DD.md and emailed to j_scott_vogel@yahoo.com
- [ ] Human-in-the-loop interrupt is respected — any irreversible action (send email, update work item) during an autonomous run routes through the approval queue
- [ ] Scheduler is configurable — frequency and trigger types can be updated via a config file without code changes
- [ ] All four trigger types (morning briefing, email webhook, hourly health check, stale program scan) are independently toggleable on/off per tenant

## Technical Notes
- Use AWS EventBridge Scheduler for cron triggers. Target: Lambda function or ECS task that bootstraps the LangGraph graph with tenant context.
- Email webhook: use Nylas webhook subscription on `message.created` event. POST to an API Gateway endpoint that invokes the graph asynchronously.
- LangGraph graph must be invoked with: (1) correct SystemMessage, (2) tenant ID, (3) trigger type as metadata so Milo knows why she woke up.
- Idempotency: before any action in an autonomous run, call memory__search to check if the same action was taken in the last 24 hours.
- Stall recovery: use LangGraph's `recursion_limit` config (set to 50). On RecursionError, catch and invoke handoff__human.
- Timezone: store tenant timezone in config. Default to America/Chicago.
- Config file: store trigger settings in tenant storage at config/scheduler.json. Schema: { "morning_briefing": { "enabled": true, "time": "07:00", "timezone": "America/Chicago" }, "email_webhook": { "enabled": true }, "hourly_health_check": { "enabled": true }, "stale_program_scan": { "enabled": true, "threshold_days": 7 } }
- All runs must be logged. Write to storage at logs/daily_run_YYYY-MM-DD.md.
- Do NOT use polling for email — use webhooks only to avoid rate limits and unnecessary Lambda invocations.
