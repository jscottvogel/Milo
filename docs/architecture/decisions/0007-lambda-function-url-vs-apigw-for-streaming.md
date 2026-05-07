# ADR 0007: Lambda Function URLs vs API Gateway for SSE Streaming

## Status
Accepted

## Context
Milo Phase 6 requires deploying the FastAPI application to AWS Lambda. Our core agent interactions rely heavily on Server-Sent Events (SSE) to stream LLM responses and tool execution updates in real-time to the frontend.

Traditionally, REST APIs on AWS Lambda are exposed via API Gateway. However, API Gateway REST APIs have strict timeout limits (29 seconds) and do not support HTTP streaming natively without resorting to WebSocket APIs, which introduce significant complexity (connection state management, two-way framing) compared to simple SSE.

## Decision
We will use **AWS Lambda Function URLs with `InvokeMode: RESPONSE_STREAM`** instead of API Gateway for the `milo-poc` deployment.

## Rationale
1. **Streaming Support**: Lambda Function URLs natively support response payload streaming (chunked transfer encoding). This allows our FastAPI SSE endpoints to work out-of-the-box using the Mangum adapter and Lambda's streaming capabilities.
2. **Timeout**: Function URLs inherit the Lambda function's timeout (up to 15 minutes), resolving the 29-second API Gateway limit. This is critical for agentic operations that involve multiple sequential LLM queries and tool invocations.
3. **Simplicity**: Bypassing API Gateway reduces infrastructure complexity and cost for the PoC.
4. **Security**: We will secure the Function URL using application-level JWT validation (via AWS Cognito/Clerk), allowing us to leave the URL's native auth as `NONE`.

## Consequences
- We lose API Gateway's native features like request validation, WAF integration, and usage plans. These must be handled at the application layer or via CloudFront if we put a CDN in front of the URL later.
- Custom domain mapping requires CloudFront instead of API Gateway custom domains.
