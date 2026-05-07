# OAuth Token Expired Runbook

## Symptoms
- Agent fails to execute `gmail.read` or `gmail.send`.
- Sentry captures `401 Unauthorized` from `googleapis.com`.

## Root Cause
The OAuth Refresh Token stored in AWS SSM has been revoked by the user, or Google has invalidated the session due to a security event or password change.

## Resolution
1. Notify the user via the UI to re-authenticate their Gmail integration.
2. The UI will hit `POST /v1/integrations/gmail/connect` which writes a fresh token payload to SSM.
3. The Agent will pick up the new token automatically on the next turn.
