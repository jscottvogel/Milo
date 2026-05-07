# Customer Deletion Runbook

## Policy
Customers have the right to request full data deletion (GDPR/CCPA). Milo retains data for 60 days post-cancellation unless a hard delete is explicitly requested.

## Procedure for Hard Deletion
1. **Locate Tenant**: Find the `tenant_id` in the database.
2. **Revoke Integrations**: Delete all associated OAuth tokens from AWS SSM Parameter Store:
   ```bash
   aws ssm delete-parameter --name "/milo/tenants/{tenant_id}/integrations/gmail/token"
   ```
3. **Database Purge**: Connect to the RDS instance and execute the cascading delete:
   ```sql
   DELETE FROM tenants WHERE id = 'tenant_id';
   ```
4. **Verify**: Ensure Stripe customer is marked as canceled and billing has ceased.
