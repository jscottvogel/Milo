# UI ↔ DB Reconciliation — Program Hierarchy Completeness

**Date:** 2026-05-08T17:34:26.324202
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
The Milo program board renders the work item hierarchy from the DB. A gap audit has identified that the DB is partially populated and contains misaligned data. The UI therefore shows an incomplete and inaccurate program board.

Current DB state (confirmed via work_item__read):
  ✅ 1 objective
  ✅ 3 outcomes (no children linked)
  ✅ 4 key results (not linked to outcomes — floating under objective)
  ✅ 4 initiatives (not linked to outcomes — floating under objective)
  ⚠️  20 projects — misaligned (future feature names placed under wrong build-phase initiatives)
  ❌ 0 workstreams
  ❌ 0 milestones
  ❌ 0 risks
  ❌ 0 decisions

The hydration manifest is stored at: hydration_runs/run-001/manifest.json

This manifest contains the correct, fully-specified hierarchy extracted from the source documents.

PROBLEMS TO FIX:

PROBLEM 1 — Parent Linkage Broken
Key results and initiatives were created as direct children of the objective instead of being linked to their correct parent outcomes. The UI renders hierarchy by parent_id. If parent_id points to the objective instead of the correct outcome, the board collapses everything to the top level and the outcome layer appears empty.

PROBLEM 2 — Misaligned Projects
The 20 existing projects under the 4 initiatives are future product capability features (e.g. 'Predictive Risk Scoring', 'Sentiment Analysis on Communications') — not build-phase projects. They were written in a prior hydration run that used the wrong source section.

PROBLEM 3 — Missing Layers
Workstreams, milestones, risks, and decisions were never written to the DB. The manifest contains all of them.

WHAT YOU NEED TO BUILD:

COMPONENT 1 — Reconciliation Diff Engine
Build a reconciliation tool that: (1) Reads the hydration manifest JSON from storage, (2) Reads the full current work item tree from the DB, (3) Produces a diff report with to_create, to_reparent, to_archive, and already_correct buckets, (4) Shows the diff to the user before making any changes, (5) On user confirmation, executes the reconciliation: archive misaligned entities, re-parent mislinked entities, create missing entities layer by layer.

COMPONENT 2 — Parent Linkage Validator
Add a background validator that runs after every hydration or work_item__update call and checks that every entity type has a valid parent type. If a violation is found, log it to hydration_runs/{run_id}/validation_errors.json and surface a warning banner in the UI.

COMPONENT 3 — Archive vs Delete Toggle
The UI currently has no way to distinguish active vs archived work items. Add status='archived' filter, a toggle to show/hide archived items, visual treatment for archived items (strikethrough + grey), and bulk archive action.

## Acceptance Criteria
- [ ] After reconciliation, the program board shows all 8 hierarchy layers with correct parent-child nesting
- [ ] Key results appear under their correct outcome (not under the objective)
- [ ] Initiatives appear under their correct outcome (not under the objective)
- [ ] The 20 misaligned projects are archived and no longer visible by default
- [ ] All 11 workstreams are present under correct initiative parents
- [ ] All 14 milestones are present under correct workstream parents
- [ ] All 8 risks are present and visible in the risk register
- [ ] All 7 decisions are present and visible in the decision log
- [ ] The reconciliation diff is shown to the user before any writes
- [ ] Parent linkage validator runs post-reconciliation and reports 0 violations
- [ ] Re-running reconciliation on a correct DB produces a diff with 0 items in to_create, to_reparent, and to_archive

## Technical Notes
Use entity status='archived' for soft deletes — no hard deletes. Reconciliation must be idempotent — safe to run multiple times. Match entities by name + type + parent_name (not ID) when diffing manifest vs DB. Batch size for parallel creates must not exceed 5 simultaneous calls to work_item__update. All reconciliation runs must be logged to hydration_runs/{run_id}/reconciliation_log.json. Hydration manifest is at hydration_runs/run-001/manifest.json.
