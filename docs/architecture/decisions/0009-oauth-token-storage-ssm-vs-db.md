# ADR 0009: OAuth Token Storage - SSM vs DB

## Status
Accepted

## Context
Milo connects to third-party services (e.g., Gmail, QuickBooks) on behalf of tenants using OAuth 2.0. These flows yield highly sensitive access and refresh tokens. We needed to decide where to store these tokens: the primary PostgreSQL database or AWS Systems Manager (SSM) Parameter Store.

## Decision
We chose to store third-party OAuth access and refresh tokens in **AWS Systems Manager (SSM) Parameter Store** using `SecureString` types rather than our primary relational database.

## Rationale
1. **Security & Encryption**: SSM `SecureString` automatically encrypts the payload at rest using AWS KMS. While we could encrypt database columns, offloading this responsibility to a managed AWS service heavily reduces our risk footprint and ensures key rotation and management are handled externally.
2. **Access Control**: By using SSM, we can write fine-grained IAM policies. The Lambda function running the Agent can be granted read-only access exclusively to `/milo/tenants/{tenant_id}/integrations/*` paths during execution, limiting the blast radius of any code execution vulnerability.
3. **Auditability**: AWS CloudTrail automatically logs all access to SSM Parameters, providing out-of-the-box compliance tracking for who (or what process) accessed tenant tokens.
4. **State Separation**: Keeping highly ephemeral and sensitive integration tokens out of the primary relational database keeps database backups "cleaner" from a compliance perspective. If a DB snapshot is leaked, the attacker still cannot access external tenant integrations without the KMS keys and AWS context.

## Consequences
- **Latency**: Fetching tokens from SSM adds a slight network latency (~10-30ms) to the start of an agent run. Since agent runs are asynchronous and already bound by LLM latency, this overhead is completely acceptable.
- **Local Development**: Local development requires mocking the `boto3` SSM client or ensuring developers have AWS credentials configured to write to a sandbox AWS account, which slightly increases local setup complexity.
