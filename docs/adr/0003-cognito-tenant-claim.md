# ADR 0003: Storing Tenant ID in Cognito Custom Attributes

## Status
Accepted

## Context
In a multi-tenant platform, every authenticated request must be securely scoped to a specific tenant. Traditional architectures often involve querying the database on every request to resolve a user's `tenant_id` from a sessions or memberships table, adding latency and load to the database.

Amazon Cognito allows the configuration of custom attributes on user profiles, which are then embedded as claims within the JWT ID tokens issued upon successful authentication.

## Decision
We will store the user's `tenant_id` in an immutable Cognito custom attribute (`custom:tenant_id`). The FastAPI authentication middleware will extract this claim directly from the verified JWT and inject it into the request context. 

## Consequences

**Positive:**
- **Zero-DB Auth**: The API can resolve and authorize the `tenant_id` purely via cryptographic verification of the JWT, eliminating a database round-trip for every request.
- **Security**: Because the JWT is signed by Cognito and the `custom:tenant_id` attribute is marked as immutable, the client cannot spoof their tenant affiliation.

**Negative:**
- **Immutability Constraints**: A single Cognito user profile cannot seamlessly switch between multiple tenants. In Milo's current B2B model, a user identity is tightly coupled to a single organizational tenant, so this constraint aligns with our domain model.
- **Admin API Dependency**: Setting the `tenant_id` upon tenant creation requires an out-of-band call to the AWS Cognito Admin API (`admin_update_user_attributes`), introducing a minor operational dependency during the onboarding flow.
