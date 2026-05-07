# AWS Bedrock Throttling Runbook

## Symptoms
- CloudWatch Alarm: API p95 latency > 5s.
- Sentry errors showing `ThrottlingException` from Bedrock.
- Users report the chat is "hanging" or returning 500 errors.

## Root Cause
The Milo agent is executing too many concurrent inference calls or exceeding the tokens-per-minute (TPM) limits on `anthropic.claude-3-5-sonnet`.

## Resolution
1. **Immediate**: Check AWS Service Quotas for Bedrock in `us-east-1`. Request a quota increase for Provisioned Throughput or On-Demand TPM.
2. **Application Level**: Ensure `Tenacity` retry blocks in `AgentRunner` are correctly implementing exponential backoff.
3. **Failover**: If `us-east-1` is totally degraded, update the `boto3` client initialization to fallback to `us-west-2` where Bedrock is also available.
