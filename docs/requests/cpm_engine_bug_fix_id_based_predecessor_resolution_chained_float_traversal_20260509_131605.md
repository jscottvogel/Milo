# CPM Engine Bug Fix — ID-Based Predecessor Resolution & Chained Float Traversal

**Date:** 2026-05-09T13:16:05.877950
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
The `program__critical_path` tool was implemented but is not functioning correctly. Two specific defects have been identified through live testing:

**Defect 1 — Dependency Resolution by Name String (Not ID)**
Dependencies are stored as name strings (e.g., "Phase 2 Complete") rather than resolved entity UUIDs. The CPM engine cannot traverse the predecessor graph because it has no mechanism to look up a work item by name and resolve it to an ID. As a result, the DAG is never constructed — the engine treats every node as a root node with no predecessors.

**Defect 2 — Float Computed Independently Per Item (Not Chained)**
Because the DAG is not traversed, the engine computes float for each work item in isolation relative to the program end date, rather than performing a true CPM forward/backward pass. This produces artificially large float values (270–299 days) for items that are actually on the critical path with zero float.

**Impact:** The `program__critical_path` tool returns misleading results. A 303-day fully sequential program with 15 chained gates shows most items with 270+ days of float, when the true answer is zero float on every node in the chain.

**Root Cause:** The dependency field stores human-readable name strings. The CPM engine needs to resolve these to UUIDs before building the DAG, or dependencies need to be stored as UUIDs at write time.

## Acceptance Criteria
- [ ] When dependencies are stored as name strings, the engine resolves each name to a work item UUID via a name-lookup query before constructing the DAG.
- [ ] If a dependency name cannot be resolved to a UUID, the engine logs a warning and skips that edge (does not crash or silently ignore all edges).
- [ ] The CPM forward pass correctly computes Early Start (ES) and Early Finish (EF) for every node by traversing predecessor edges in topological order.
- [ ] The CPM backward pass correctly computes Late Start (LS) and Late Finish (LF) for every node by traversing successor edges in reverse topological order.
- [ ] Float for each node is computed as LS - ES (or LF - EF), not as (program_end - item_due_date).
- [ ] Nodes with zero float are correctly flagged as critical path nodes in the response.
- [ ] A fully sequential 15-node chain (Phase 0 → Phase 1 → ... → Phase 12B) returns zero float on every node.
- [ ] The what-if slip scenario correctly propagates a slip on one node forward through all successor nodes and returns updated EF and float values for the entire downstream chain.
- [ ] Circular dependency detection raises a clear error identifying the cycle before attempting DAG traversal.
- [ ] The tool is re-tested against the Milo Platform program (program ID available in work item store) and produces a chained zero-float critical path from Phase 0 Complete → Phase 12B Complete.

## Technical Notes
Dependencies are currently written via `work_item__update` payload field `dependencies` as a list of name strings (e.g., ["Phase 2 Complete — v0.1 Tagged"]). The fix can go one of two directions: (1) Resolve names to UUIDs at read time inside the CPM engine using a name-index lookup, or (2) Change `work_item__update` to accept and store UUIDs in the dependencies field and backfill existing records. Option 1 is lower risk and faster. The Milo Platform program has 15 sequential milestone gates fully wired with name-string dependencies — use this as the regression test case. Program end date is March 8, 2027.
