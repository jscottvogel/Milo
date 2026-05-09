# Dependency & Critical Path Analysis Engine

**Date:** 2026-05-09T12:49:48.244395
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo can currently store dependencies between work items (tasks, milestones, projects) as string references in the work item payload. However, she has no ability to compute the critical path, identify blocking relationships, or surface schedule risk based on dependency chains.

This capability is a core program management function. Without it, Milo cannot answer questions like:
- "What is the longest path to delivery?"
- "If Task X slips 5 days, what else moves?"
- "What is currently blocking Milestone Y?"
- "Which tasks have zero float?"

The goal is to build a dependency graph engine that Milo can invoke at any time to compute the critical path across a program's work items and surface actionable schedule risk.

## Acceptance Criteria
- [ ] Milo can invoke a tool (e.g. `program__critical_path`) with a project or program ID and receive a structured critical path result.
- [ ] The engine reads all work items and their `dependencies` fields to construct a directed acyclic graph (DAG).
- [ ] The engine computes forward and backward pass to determine Early Start, Early Finish, Late Start, Late Finish, and Float for each task.
- [ ] Tasks with zero float are flagged as critical path nodes.
- [ ] The engine detects and reports circular dependencies as an error condition.
- [ ] The engine returns a list of blocking relationships: for each task, what it is blocked by and what it is blocking.
- [ ] Milo can ask 'what happens if task X slips N days?' and receive a downstream impact list.
- [ ] Results include a human-readable summary Milo can include in briefings or emails.
- [ ] The engine handles missing due dates gracefully (treats as unknown float, flags for attention).
- [ ] Critical path results are written to memory after each computation for audit trail.
- [ ] Performance: must handle programs with up to 500 work items in under 5 seconds.
- [ ] Milo can trigger this automatically during daily briefing if any dependency changes were detected in the last 24 hours.

## Technical Notes
- Dependencies are currently stored as a list of strings (entity names) in the work item payload. The engine will need to resolve these names to IDs for graph construction — consider migrating to ID-based references for reliability.
- Recommended graph library: NetworkX (Python) for DAG construction and critical path computation.
- CPM (Critical Path Method) algorithm: standard forward/backward pass. Do not use PERT unless probabilistic durations are added later.
- The 'what-if slip' feature should re-run the forward pass with the modified duration and diff the result against the baseline.
- Store the computed critical path as a JSON blob in storage (e.g. `program_data/{program_id}/critical_path_latest.json`) so Milo can reference it without recomputing every time.
- Expose as a new tool: `program__critical_path(program_id, what_if_task_id=None, what_if_slip_days=None)`
- Consider a lightweight visualization output (Mermaid diagram or ASCII Gantt) that Milo can embed in documents or emails.
