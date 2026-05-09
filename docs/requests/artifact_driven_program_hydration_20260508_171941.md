# Artifact-Driven Program Hydration

**Date:** 2026-05-08T17:19:41.148775
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo is an agentic AI coordinator with a work item system that supports an 8-layer hierarchy: objective → outcome → key_result → initiative → project → workstream → milestone → task, plus associated entities: risk, decision, change_request, stakeholder, action_item. The UI renders this hierarchy as a program board.

Currently the board is sparsely populated — only the top-level objective, 4 key results, 4 initiatives, and 1 stakeholder exist. The full program detail from uploaded specification documents has NOT been written to the work item system.

Two source documents are in tenant storage:
- uploads/2026-05-08/Milo_Antigravity_Build_Prompts.md
- uploads/2026-05-08/Milo_Platform_Build_Specification.docx

These documents contain the full program definition including phases, workstreams, milestones, risks, decisions, and acceptance criteria.

**Root Cause:** When a user uploads a program specification document and asks Milo to "populate the program," Milo calls work_item__update in batches but the UI does not reflect the full hierarchy. This happens because:
1. Milo's tool call batches are large and some calls silently fail or are dropped when too many are fired simultaneously
2. There is no confirmation loop — Milo does not verify that each entity was actually created before moving to the next layer
3. Parent IDs from newly created entities are needed before children can be created, but Milo sometimes proceeds without waiting for confirmed IDs
4. There is no "hydration status" visible to the user — they cannot tell what was created vs. what failed

**COMPONENT 1 — Sequential Hydration Engine**
Build a hydration orchestrator that:
1. Reads the work item tree top-down before writing anything
2. Creates entities layer by layer, strictly in this order: objective → outcome → key_result → initiative → project → workstream → milestone → task → risk → decision → change_request → stakeholder → action_item
3. After each work_item__update call, confirms the returned entity ID before proceeding to create any children of that entity
4. Retries failed creates up to 3 times with exponential backoff before marking as failed
5. Logs a hydration manifest: { entity_type, name, status, id, parent_id, attempt_count } for every entity attempted
6. Never uses a placeholder or assumed ID — only uses confirmed returned IDs as parent_id values

**COMPONENT 2 — Hydration Status Panel (UI)**
Add a "Program Hydration" status panel to the UI that shows:
- Total entities attempted vs. created vs. failed
- A collapsible tree showing each entity and its creation status (✅ created / ⚠️ retrying / ❌ failed)
- A "Retry Failed" button that re-attempts only failed entities
- A "Re-hydrate from Source" button that re-reads the source documents and re-runs the full hydration (idempotent — skips entities that already exist by name+type+parent match)
- Timestamp of last hydration run

**COMPONENT 3 — Idempotent Upsert Logic**
The work_item__update tool must support idempotent upserts:
- Before creating a new entity, check if an entity with the same name + type + parent_id already exists
- If it exists: update it with any new fields, return existing ID
- If it does not exist: create it, return new ID
- This prevents duplicate entities on re-hydration runs

**COMPONENT 4 — Document-to-Program Extraction Prompt**
When a user uploads a specification document, Milo must run a structured extraction pass that produces a hydration manifest JSON before writing anything to the work item system. The manifest format:
```json
{
  "objective": { "name": "...", "description": "...", "status": "..." },
  "outcomes": [ { "name": "...", "description": "...", "status": "..." } ],
  "key_results": [ { "name": "...", "parent": "outcome_name", ... } ],
  "initiatives": [ { "name": "...", "parent": "outcome_name", ... } ],
  "projects": [ { "name": "...", "parent": "initiative_name", ... } ],
  "workstreams": [ { "name": "...", "parent": "project_name", ... } ],
  "milestones": [ { "name": "...", "parent": "workstream_name", "due_date": "...", ... } ],
  "tasks": [ { "name": "...", "parent": "milestone_name", ... } ],
  "risks": [ { "title": "...", "likelihood": 1-5, "impact": 1-5, "mitigation": "...", "parent": "project_name" } ],
  "decisions": [ { "title": "...", "decision_text": "...", "parent": "project_name" } ],
  "stakeholders": [ { "name": "...", "role": "...", "email": "...", "influence": "...", "interest": "..." } ]
}
```
Milo must show this manifest to the user for confirmation before writing to the work item system.

**COMPONENT 5 — Artifact Linkage**
Every work item created from a source document must store:
- source_document: filename of the originating document
- source_section: the section/heading it was extracted from
- hydration_run_id: UUID of the hydration run that created it

Store these in metadata_json on the work item.

## Acceptance Criteria
- [ ] After hydration, the UI program board shows all 8 hierarchy layers populated with data from the spec documents
- [ ] Every entity has a confirmed ID before any child entity is created
- [ ] Re-running hydration on an already-populated program does not create duplicates
- [ ] Failed entity creates are retried up to 3 times and reported in the hydration status panel
- [ ] The hydration manifest JSON is shown to the user before any writes occur, with a confirm/cancel prompt
- [ ] All created entities have source_document, source_section, and hydration_run_id in metadata_json
- [ ] The 'Retry Failed' button successfully re-attempts and creates previously failed entities
- [ ] Hydration of the full Milo Platform spec (both documents) produces at minimum: 1 objective, 3+ outcomes, 4+ key results, 4+ initiatives, 10+ projects (one per build phase), 6+ workstreams, 10+ milestones, 5+ risks, 5+ decisions, 1+ stakeholders
- [ ] Hydration completes within 60 seconds for a 200-entity program
- [ ] No unhandled exceptions — all failures are caught and reported in the hydration manifest

## Technical Notes
1. Hydration engine must be async — do not block the UI thread
2. Parent ID resolution must use a local name→ID map built during the hydration run, not re-queried from the API on each call
3. Batch size for parallel creates must not exceed 5 simultaneous calls to work_item__update
4. The hydration manifest JSON must be stored in tenant storage at hydration_runs/{run_id}/manifest.json after each run
5. Must integrate with existing work_item__read and work_item__update tools — no new database tables required
6. Source documents are located at:
   - uploads/2026-05-08/Milo_Antigravity_Build_Prompts.md
   - uploads/2026-05-08/Milo_Platform_Build_Specification.docx
7. Strictly enforce layer-by-layer creation order: objective → outcome → key_result → initiative → project → workstream → milestone → task → risk → decision → change_request → stakeholder → action_item
8. Use exponential backoff on retries: 1s, 2s, 4s before marking as failed
