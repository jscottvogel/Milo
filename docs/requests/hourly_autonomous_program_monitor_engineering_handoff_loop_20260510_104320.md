# Hourly Autonomous Program Monitor & Engineering Handoff Loop

**Date:** 2026-05-10T10:43:20.552997
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
## Overview
Milo needs a new scheduled job — independent of the daily morning briefing — that wakes up every hour and autonomously evaluates program health and capability gaps. When a gap or issue is identified, Milo writes a structured engineering handoff document and emails it to j_scott_vogel@yahoo.com.

This is a **separate Lambda + EventBridge Scheduler job** from the daily briefing. It runs on its own cron, has its own handler, and its own idempotency logic.

---

## What Milo Does Each Hour

### Step 1 — Read Program State
- Call `work_item__read` on all root items with `include_children: true`
- Identify: overdue tasks, stalled milestones, unresolved risks, missing owners, stale statuses

### Step 2 — Audit Capabilities
- Search episodic memory for the current capability map (20-capability target list)
- Compare against confirmed COMPLETED_ handoffs in `engineering_requests/`
- Identify any capability that is: missing, not yet handed off, or handed off but not confirmed live

### Step 3 — Identify Gaps
For each gap found:
- Check memory to confirm this gap has NOT already been filed in the last 24 hours (idempotency guard)
- If new: proceed to Step 4
- If already filed within 24h: skip

### Step 4 — Write Engineering Handoff
- Use `developer__handoff` tool to generate a structured requirements doc
- Include: title, full description, acceptance criteria, technical notes
- Save a copy to `engineering_requests/{slug}.md` via `storage__write`

### Step 5 — Email Handoff to Owner
- Send the full handoff spec to `j_scott_vogel@yahoo.com` via `email__send`
- Subject: `[Milo Handoff] {capability name} — {date}`
- Body: full markdown spec inline

### Step 6 — Write Memory Entry
- Write a memory entry (kind: `event`) recording:
  - What gap was identified
  - What handoff was filed
  - Timestamp
  - Idempotency key so the same handoff is not re-filed within 24h

---

## Trigger Cadence
- **Every 1 hour**, 24/7
- Implemented via **AWS EventBridge Scheduler** (separate rule from the daily briefing)
- Invokes a **dedicated AWS Lambda** handler

---

## Idempotency Rules
- Before filing any handoff, Milo calls `memory__search` for the capability name
- If a matching handoff event exists with a timestamp within the last 24 hours → skip
- This prevents duplicate emails and duplicate handoff docs on every hourly run
- Each handoff email is only sent once per gap per 24-hour window

---

## Scope
This job does NOT replace or modify the daily morning briefing. It is a completely independent job with its own:
- EventBridge Scheduler rule
- Lambda handler
- Memory namespace / idempotency keys
- Email subject prefix `[Milo Handoff]` (vs briefing prefix `[Milo Briefing]`)

## Acceptance Criteria
- [ ] A new AWS EventBridge Scheduler rule fires every 60 minutes, independent of the daily briefing rule
- [ ] A dedicated Lambda handler is invoked — separate function from the briefing Lambda
- [ ] Each run reads all root work items with children via work_item__read
- [ ] Each run audits engineering_requests/ storage for COMPLETED_ vs pending handoffs
- [ ] Each run searches episodic memory for the 20-capability target list and compares against confirmed live capabilities
- [ ] For each identified gap, memory__search is called first — if a handoff was filed for this gap within the last 24 hours, it is skipped
- [ ] For new gaps, developer__handoff is called with a fully structured spec (title, description, acceptance criteria, technical notes)
- [ ] The handoff is saved to engineering_requests/{slug}.md via storage__write
- [ ] An email is sent to j_scott_vogel@yahoo.com with subject [Milo Handoff] {capability} — {date} and the full spec in the body
- [ ] A memory entry (kind: event) is written after each handoff is filed, recording the gap name, timestamp, and idempotency key
- [ ] No duplicate emails are sent for the same gap within a 24-hour window
- [ ] The job runs silently — no chat output, no push notification unless a new handoff is filed
- [ ] The job is independently togglable in tenant settings without affecting the daily briefing
- [ ] End-to-end test: manually trigger the Lambda, confirm it identifies at least one gap, files a handoff, emails j_scott_vogel@yahoo.com, and writes a memory entry

## Technical Notes
Architecture: AWS EventBridge Scheduler (cron: rate(1 hour)) → Lambda (milo-hourly-monitor) → Milo tool chain

- Reuse existing Milo tool chain — no new integrations needed
- Lambda must be idempotent — safe to retry
- Separate IAM role from briefing Lambda (least privilege)
- Idempotency key format: `hourly_handoff_{capability_slug}_{YYYY-MM-DD}` — one handoff per capability per calendar day max
- Email subject prefix: [Milo Handoff] — distinct from [Milo Briefing]
- Tenant config: on/off toggle stored in DB, read at Lambda invocation time
- Do NOT modify the daily briefing Lambda or its EventBridge rule
- Log all runs to CloudWatch with: run_id, gaps_found, handoffs_filed, emails_sent, skipped (idempotent)
