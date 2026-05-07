# ADR 0010: Stripe Billing Event Architecture

## Status
Accepted

## Context
Milo Phase 9 introduces the architecture for Stripe billing. As a SaaS platform, we need to robustly consume Stripe webhooks (e.g., `invoice.paid`, `customer.subscription.updated`) to update our internal `Tenant.subscription_status`.

## Decision
We have decided to use an **EventBridge-driven architecture** for processing Stripe Webhooks instead of direct API Gateway to Lambda synchronous processing.

The architecture is as follows:
1. **API Gateway / Lambda Function URL**: Exposes a public `/v1/webhooks/stripe` endpoint.
2. **Webhook Receiver (FastAPI)**: Validates the Stripe signature using our `STRIPE_WEBHOOK_SECRET`.
3. **EventBridge**: The webhook receiver immediately publishes the validated event payload to an AWS EventBridge custom bus and returns `200 OK` to Stripe.
4. **SQS Dead Letter Queue / Retry**: EventBridge routes the event to an SQS queue which triggers a worker Lambda.
5. **Worker Lambda**: Actually processes the event (e.g., updating the database).

## Rationale
1. **Resiliency**: Stripe expects webhooks to be acknowledged quickly. If our database is under load or undergoing maintenance, processing synchronously could result in timeouts. Offloading to EventBridge ensures we acknowledge Stripe immediately.
2. **Idempotency & Retries**: By putting the events on an SQS queue via EventBridge, AWS handles backoff and retries automatically if the database update fails.
3. **Decoupling**: EventBridge allows us to easily fan-out Stripe events in the future (e.g., sending an analytics event to a data warehouse when `invoice.paid` occurs) without touching the core API code.

## Consequences
- Requires provisioning EventBridge rules and SQS queues in our `packages/cdk` infrastructure (WorkerStack).
- The `milo-poc` currently skips the physical infrastructure for webhooks since billing is stubbed, but this pattern guarantees we are production-ready for Phase 10+.
