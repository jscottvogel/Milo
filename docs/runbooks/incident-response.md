# Milo Incident Response Runbook

## Overview
This document outlines the standard operating procedure for critical incidents involving the Milo Agent Platform.

## Severity Levels
- **SEV-1**: Critical API outage, database failure, or mass agent misbehavior.
- **SEV-2**: Elevated API errors, latency spikes, or failed billing webhooks.
- **SEV-3**: Minor UX bugs, intermittent third-party integration errors.

## Escalation Path
1. On-call engineer is paged via PagerDuty (triggered by CloudWatch Alarms).
2. Triage via Sentry (`api` or `web` projects) and CloudWatch Logs (`/aws/lambda/MiloApiStack-*`).
3. Communicate status to customers via Statuspage.
4. Escalate to platform lead if resolution > 30m.

## Immediate Mitigation
- If the agent is hallucinating or executing dangerous actions, immediately sever API keys or push the `milo-poc` emergency kill-switch via AWS Systems Manager.
