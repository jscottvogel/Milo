# Daily Briefing Scheduler — AWS EventBridge + Lambda

**Date:** 2026-05-09T06:44:24.602600
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Every morning at a configured time (default 7:00 AM tenant local time), Milo must automatically compose and send a structured daily briefing to the tenant's primary email address. The job reads unread emails, calendar events (today + 7 days), open work items (risks, overdue tasks, upcoming milestones), evaluates all trigger rules, composes a structured briefing, sends it via Nylas, and writes the event to episodic memory. Scheduling is handled by AWS EventBridge Scheduler triggering an AWS Lambda function. This replaces any prior references to Vercel Cron or pg_cron. The briefing toggle and send time are configurable per tenant in Settings → Persona.

## Acceptance Criteria
- [ ] EventBridge Scheduler fires the Lambda at the correct tenant local time daily
- [ ] Lambda reads unread emails, calendar (today + 7 days), open work items, and trigger rules
- [ ] Briefing email is sent to tenant primary address via Nylas in the specified format
- [ ] Briefing event is written to episodic memory after successful send
- [ ] Tenant can configure send time and timezone in Settings → Persona
- [ ] Tenant can toggle the briefing on/off in Settings → Persona
- [ ] EventBridge rule is updated automatically when tenant changes send time or timezone
- [ ] Lambda execution role follows least-privilege IAM policy
- [ ] Briefing is skipped (not failed) if tenant toggle is off

## Technical Notes
Deploy on AWS. Use AWS EventBridge Scheduler (not Vercel Cron or pg_cron) to trigger a Lambda function daily. Lambda reuses the existing Milo tool chain — no new integrations needed. Decide between one Lambda per tenant vs. single Lambda with tenant fan-out based on scale. EventBridge rule must be created or updated whenever a tenant changes their send time or timezone setting. IAM role for Lambda should be least-privilege. Stack: AWS Lambda, AWS EventBridge Scheduler, Nylas (email send), existing episodic memory write tool.
