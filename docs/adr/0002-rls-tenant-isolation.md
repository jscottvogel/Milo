# 0002. Row-Level Security for Tenant Isolation

Date: 2026-05-07

## Context
Milo is a B2B SaaS platform that operates as a multi-tenant application. Data leakage between tenants is a critical security vulnerability. We need a robust mechanism to guarantee that a user from Tenant A cannot query or mutate data belonging to Tenant B, even if there is a bug in the application logic.

## Decision
We will use **PostgreSQL Row-Level Security (RLS)** as our primary defense-in-depth mechanism for tenant isolation, in combination with the standard application-level `tenant_id` WHERE clauses.

1. **Schema design**: Every table containing tenant data MUST include a `tenant_id` foreign key.
2. **RLS Policy**: Every such table will have an RLS policy applied:
   ```sql
   ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_isolation_policy ON {table}
       USING (tenant_id = current_setting('app.tenant_id')::uuid);
   ```
3. **Application Context**: The SQLAlchemy `db_session` context manager will issue `SET LOCAL app.tenant_id = :tenant_id` before yielding a session. This ensures that every query running within that session is automatically scoped to the active tenant.

## Consequences
**Pros:**
- **Defense in depth**: Even if an engineer forgets to add `.filter_by(tenant_id=...)` to an ORM query, the database will automatically filter the results.
- **Simplicity**: No need for complex logical shards or per-tenant schemas.

**Cons:**
- **Connection pooling overhead**: `SET LOCAL` must be executed on the connection every time a session is checked out of the pool.
- **Tooling friction**: Database GUIs (like DBeaver or pgAdmin) will not return any rows from RLS-enabled tables unless the user manually runs `SET app.tenant_id = '...'` in their SQL scratchpad.

## Status
Accepted.
