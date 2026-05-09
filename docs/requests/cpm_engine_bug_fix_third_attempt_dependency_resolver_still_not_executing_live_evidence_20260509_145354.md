# CPM Engine Bug Fix — Third Attempt: Dependency Resolver Still Not Executing (Live Evidence)

**Date:** 2026-05-09T14:53:54.423235
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
## Background

This is the **third handoff** for the same root bug. The CPM engine (`program__critical_path`) has been tested live after each claimed fix and has failed every time. The DAG remains completely disconnected on every run.

### History
- **Handoff #1** (`dependency_critical_path_analysis_engine_20260509_124948.md`): Original CPM engine spec filed. Engine built but DAG was flat — all nodes treated as roots.
- **Handoff #2** (`cpm_engine_bug_fix_follow_up_partial_fix_verification_remaining_defects_20260509_133907.md`): Partial fix claimed. Live test showed 3 remaining defects: name→UUID resolution incomplete, negative float on outcome nodes, wrong node types returned on critical path.
- **Handoff #3 (this one)**: Engineering claimed `.startswith()` fix in `packages/agent/agent/tools/program.py` resolved the name→UUID resolution issue. **Live test immediately after the fix was deployed proves it did not.**

---

## Live Test Evidence (Post-.startswith() Fix)

Every node still returns `early_start: 0`. The `critical_path` array returns only the root objective node (1 node, not 15). Zero nodes have `is_critical: true`. The DAG is treating every milestone as a disconnected root with no predecessors.

| Signal | Expected | Actual |
|---|---|---|
| `critical_path` array length | 15 phase-gate milestones | **1 (root objective only)** |
| Phase 0 Complete `early_start` | > 0 | **0** |
| Phase 1 Complete `early_start` | > 0 | **0** |
| Phase 12B Complete `float` | 0 (critical) | **285** |
| Nodes with `is_critical: true` | 15 | **0** |

---

## Root Cause Hypothesis

The `.startswith()` logic may exist in the code but is **not being reached** before DAG construction. The most likely causes, in order of probability:

1. **The fix was not deployed to the environment the endpoint is hitting.** Unit tests pass locally against mocks; the live service is running stale code.
2. **The resolver function is called after DAG construction**, not before. The DAG is built with unresolved string dependency names, which never match any node UUID, so no edges are added.
3. **The dependency strings stored in the database are null or empty** for the nodes being queried. The resolver has nothing to resolve. This can be verified by querying the `dependencies` field directly on any milestone work item.
4. **The `.startswith()` direction is inverted.** The code may be checking `dependency_string.startswith(node_name)` instead of `node_name.startswith(dependency_string)`.

---

## What a Correct Fix Looks Like

The resolver must:

1. **Run before DAG construction** — produce a complete `name_string → UUID` map for all nodes in the program tree.
2. **Use fuzzy/prefix matching** — `node_name.startswith(dep_string)` OR `dep_string in node_name` to handle truncated dependency strings like `"Phase 2 Complete"` matching `"Phase 2 Complete — Cognito Auth + Stripe Billing + Tenant Onboarding Wizard"`.
3. **Inject resolved UUIDs as predecessor edges** into the DAG before the forward pass runs.
4. **Log resolver output** — emit a debug log line for every resolved and every unresolved dependency string so failures are visible without a full debugger session.

## Verification Protocol

Do NOT mark this fixed until the following live API call returns correctly:

```
program__critical_path(program_id="<milo_platform_program_id>")
```

Expected response:
- `critical_path` array contains **15 nodes** (Phase 0 Complete → Phase 12B Complete)
- At least one node has `early_start > 0`
- At least one node has `is_critical: true` and `float: 0`
- The root objective node is **not** the only item in `critical_path`

Milo will re-run the live test immediately upon notification. No self-certification.

## Acceptance Criteria
- [ ] The live `program__critical_path` API call returns a `critical_path` array containing exactly 15 phase-gate milestone nodes (Phase 0 Complete through Phase 12B Complete).
- [ ] At least one node in the response has `early_start > 0`, proving the forward pass is traversing edges.
- [ ] At least one node has `is_critical: true` AND `float: 0`, proving the backward pass is correctly anchoring to the program end date.
- [ ] The root objective node is NOT the sole item in the `critical_path` array.
- [ ] The dependency resolver runs BEFORE DAG construction — verified by a debug log line emitted for each resolved dependency string showing the matched UUID.
- [ ] Unresolved dependency strings are logged as warnings (not silently dropped) so missing links are visible.
- [ ] The `.startswith()` or equivalent fuzzy match correctly resolves truncated strings: e.g. 'Phase 2 Complete' must match 'Phase 2 Complete — Cognito Auth + Stripe Billing + Tenant Onboarding Wizard'.
- [ ] No negative float values appear on any node (backward pass end anchor is correctly set to the program's latest due date).
- [ ] Milo independently re-runs the live test and confirms — no self-certification by engineering.

## Technical Notes
FILE: packages/agent/agent/tools/program.py

CRITICAL SEQUENCE: The resolver MUST execute in this order:
1. Fetch all nodes in the program tree (all types: milestones, tasks, workstreams, etc.)
2. Build a name→UUID lookup map
3. For each node's `dependencies` list (strings), resolve each string to a UUID using startswith/contains matching
4. Inject resolved UUID pairs as directed edges into the DAG
5. THEN run the CPM forward/backward pass

If step 4 produces zero edges, the DAG will be flat and CPM is meaningless. Add an assertion or warning log if edge count == 0 after resolution.

DEBUGGING SHORTCUT: Add a temporary endpoint or log that dumps the raw `dependencies` field from 3-4 milestone nodes directly from the database. If those fields are empty strings or null, the bug is in data, not code. If they contain strings like "Phase 2 Complete", the bug is in the resolver not running or not matching.

Previous handoff files for reference:
- docs/requests/dependency_critical_path_analysis_engine_20260509_124948.md
- docs/requests/cpm_engine_bug_fix_follow_up_partial_fix_verification_remaining_defects_20260509_133907.md
