# Remove Approval Gate from Slack Tool Calls

**Date:** 2026-05-12T10:31:34.512362
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
The `slack__send` tool is currently routed through the approval queue before execution. This causes thread starvation in the AI executor: the tool call blocks indefinitely waiting for a human approval decision that never arrives, consuming an execution slot until the iteration limit is hit and the entire agent thread halts.

Slack messages are low-risk, reversible, and time-sensitive coordination actions. Requiring approval on them defeats their purpose and introduces a systemic reliability failure in the executor. Slack tools should be treated as fire-and-forget actions — same trust tier as `email__send` — and must never block on an approval gate.

## Acceptance Criteria
- [ ] slack__send executes immediately without triggering an approval request
- [ ] slack__send returns a structured success or error response within 5 seconds
- [ ] If Slack is unreachable, slack__send returns a graceful degradation error (not a hang)
- [ ] No approval record is created in the approval queue when slack__send is called
- [ ] Regression test: calling slack__send in a multi-tool batch does not cause executor thread starvation or halt

## Technical Notes
The approval gate is likely configured at the tool-permission or middleware layer. Check the tool authorization config for `slack__send` and remove any approval-required flag. Ensure the same audit/logging that other non-approval tools use is applied so there is still a record of Slack messages sent. Compare against `email__send` configuration as the reference implementation — it degrades gracefully without blocking.
