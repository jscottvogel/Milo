# Cost Spike Runbook

## Symptoms
- CloudWatch Alarm: `Agent cost / hour > $5`.
- AWS Budgets alerts triggered.

## Root Cause
An agent might be caught in a tool-calling infinite loop, or a user is maliciously submitting max-context prompts repeatedly.

## Resolution
1. **Identify the Offender**: Query the `AgentRun` table in Postgres:
   ```sql
   SELECT tenant_id, sum(cost_usd) FROM agent_runs WHERE started_at > NOW() - INTERVAL '1 hour' GROUP BY tenant_id ORDER BY sum DESC;
   ```
2. **Mitigation**: If it is a malicious actor or runaway loop, suspend the tenant's access temporarily by updating their status in the DB.
3. **Fix the Loop**: Check Langfuse traces for the offending `thread_id` to understand why the LLM got stuck in a loop. Adjust the system prompt or tool outputs to break the cycle.
