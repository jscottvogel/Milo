# CPM Engine Bug Fix — Follow-Up: Partial Fix Verification & Remaining Defects

**Date:** 2026-05-09T13:39:07.036425
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Engineering submitted a fix for the two CPM defects filed in the previous handoff (docs/requests/cpm_engine_bug_fix_id_based_predecessor_resolution_chained_float_traversal_20260509_131605.md). Live testing against the Milo Platform program confirms the fix is **incomplete**. Three specific defects remain after the patch.

**Test Program:** Milo Platform (15-phase sequential chain, May 10 2026 → Mar 8 2027)
**Expected Result:** All 15 phase-gate milestones return float=0, is_critical=true, chained in sequence.
**Actual Result:** See defects below.

---

**Defect 1 — Name → UUID Resolution Incomplete (Partial Fix)**
The forward/backward pass is now running (early_start, early_finish, late_start, late_finish are populated — confirmed improvement). However, predecessor resolution is only working for a small subset of nodes. The majority of tasks still show early_start: 0, meaning they are being treated as root nodes with no predecessors. The DAG is partially built, not fully traversed. Name → UUID resolution is succeeding for some nodes but silently failing for others — likely a case-sensitivity, whitespace, or scope mismatch issue in the lookup.

**Defect 2 — Negative Float on Outcome-Level Items**
Two outcome nodes are returning negative float:
- "Phase 2 — Multi-Tenant SaaS": float = -1
- "Phase 3 — Paying Customers at Scale": float = -60
Negative float indicates the program end anchor date used by the backward pass is earlier than these items' due dates. The program end anchor is miscalibrated — it is likely being derived from the earliest-finishing leaf node rather than the true program end date (Mar 8 2027).

**Defect 3 — Critical Path Output Returns Wrong Nodes**
The critical path result is returning capability task names ("Email Read & Inbox Monitoring", "Email Send (Autonomous)", "Proactive Notifications & Triggers") instead of the 15 phase-gate milestones. This confirms the DAG traversal is resolving only a small island of connected nodes (the capability tasks, which happen to share similar name strings) while the phase-gate chain remains disconnected. The engine is reporting the longest connected subgraph it found, not the true program critical path.

## Acceptance Criteria
- [ ] All 15 phase-gate milestones in the Milo Platform program return float=0 and is_critical=true after the fix.
- [ ] The critical path output lists all 15 phase gates in sequential order from Phase 0 (May 10 2026) through Phase 12B (Mar 8 2027).
- [ ] Name → UUID predecessor resolution succeeds for 100% of dependency name strings — case-insensitive, whitespace-trimmed, scoped to the same program.
- [ ] Resolution failures are logged with a warning (node name, reason for failure) rather than silently treating the node as a root.
- [ ] The program end anchor for the backward pass is explicitly set to the program's due_date field, not derived from leaf node finish times.
- [ ] Negative float values are impossible when all items' due dates fall within the program window — add a validation assertion.
- [ ] The critical path output must not return capability-level tasks as phase gates — the engine must distinguish milestone/phase-gate nodes from task nodes when reporting the critical path summary.
- [ ] What-if slip scenario: slipping Phase 0 by 14 days must push the program end date by exactly 14 days and increase float on all downstream nodes by 0.
- [ ] Regression test: re-run against the original test case from the prior handoff — 15-node chain must return zero float end-to-end.
- [ ] Unit test coverage for the name → UUID resolver, including: exact match, case mismatch, leading/trailing whitespace, no match (should warn, not crash).

## Technical Notes
Prior handoff: docs/requests/cpm_engine_bug_fix_id_based_predecessor_resolution_chained_float_traversal_20260509_131605.md

The partial fix confirms the forward/backward pass logic is structurally correct — the CPM math is working where the DAG is connected. The remaining failures are all upstream of the pass: DAG construction is incomplete due to resolver gaps and a miscalibrated end anchor.

Recommended fix order:
1. Fix the name → UUID resolver first (add logging, case-insensitive match, trim whitespace, scope to program_id).
2. Fix the backward pass end anchor to use program.due_date explicitly.
3. Re-run the full 15-node chain and verify all nodes are connected before closing.

Do NOT close this ticket until the acceptance criteria regression test passes end-to-end on the live Milo Platform program.
