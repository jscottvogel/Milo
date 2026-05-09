# Milo Approval Workflow Engine — Human-in-the-Loop Decision Loop

**Date:** 2026-05-09T12:30:47.380984
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description

Milo currently uses `handoff__human` as a blunt escalation tool — it fires an alert but has no response loop. When Milo escalates a decision, the execution graph terminates and Milo goes silent until the user manually re-engages.

This capability builds a structured, bidirectional approval workflow engine that allows Milo to:
1. Escalate a decision with structured context (approve/reject/modify options)
2. Pause the LangGraph execution at an interrupt node
3. Receive the human's structured response (approve / reject / modify + notes)
4. Resume execution from the interrupt point and act on the decision

This is the critical missing link between "Milo escalates" and "Milo continues autonomously after a decision is made." Without this, every human-in-the-loop moment breaks the execution loop permanently.

Use cases include:
- Approving an email before it is sent to an external stakeholder
- Approving a budget change request
- Confirming an irreversible action (archiving a work item, closing a project)
- Approving a change request before it is logged
- Confirming a risk escalation before notifying a sponsor


## Acceptance Criteria
- [ ] Milo can call a `request_approval` tool with: title, description, options (list of strings e.g. ['approve', 'reject', 'modify']), context_payload (JSON), and urgency (low/medium/high).
- [ ] The approval request is persisted to a database table `approval_requests` with fields: id, title, description, options, context_payload, urgency, status (pending/approved/rejected/modified), response_notes, created_at, resolved_at.
- [ ] The LangGraph graph pauses execution at an `interrupt` node when an approval is pending — it does not terminate, it waits.
- [ ] The user receives a notification (email and/or UI prompt) with the approval request details and clear approve/reject/modify buttons or reply options.
- [ ] When the user responds, the approval record is updated with status + response_notes and a webhook or callback resumes the LangGraph graph from the interrupt node.
- [ ] Milo receives the structured response (status + notes) as a tool return value and continues executing the next node in the graph.
- [ ] If no response is received within a configurable timeout (default: 24 hours), Milo sends a reminder and escalates urgency to 'high'.
- [ ] If no response is received within 48 hours, Milo defaults to the safe action (reject/no-op) and logs the timeout decision to memory.
- [ ] All approval requests and responses are written to episodic memory with kind='decision' and linked to the relevant work_item_id if applicable.
- [ ] Milo can query pending approvals at session start and surface them in the daily briefing.
- [ ] The approval UI (email or web) must display: what Milo wants to do, why, what happens if approved, what happens if rejected.
- [ ] Modify option must allow the user to provide free-text notes that Milo receives and incorporates before re-attempting the action.
- [ ] Full audit trail: every approval request, response, timeout, and downstream action taken must be logged with timestamps.
- [ ] The engine must be idempotent — duplicate approval requests for the same action within 24 hours must be suppressed.

## Technical Notes

LangGraph implementation:
- Add an `approval_interrupt` node that calls `interrupt()` from `langgraph.types`
- Use LangGraph's built-in human-in-the-loop pattern: graph.invoke() pauses at interrupt, resumes via graph.invoke(Command(resume=response))
- Store the thread_id and checkpoint in the approval_requests table so the correct graph thread is resumed
- The `request_approval` tool should write the approval record and then trigger the interrupt — do not poll
- For email-based approval: generate a unique approval URL per request (e.g. /approve/{token}) that POSTs the response and triggers the graph resume
- For UI-based approval: surface pending approvals in the Milo dashboard with action buttons
- Use Postgres or equivalent for approval_requests table — must survive server restarts
- Approval tokens must be single-use and expire after 72 hours
- Consider a `approval_queue` view in the Milo UI that shows all pending, approved, rejected decisions with timestamps
- This replaces `handoff__human` for structured decisions — `handoff__human` remains for true emergencies/unstructured escalations

