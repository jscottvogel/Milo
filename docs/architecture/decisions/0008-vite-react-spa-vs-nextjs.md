# ADR 0008: Vite + React SPA vs Next.js for Frontend

## Status
Accepted

## Context
Milo Phase 7 requires scaffolding the frontend UI. The application is an AI agent workspace featuring real-time conversational streaming (SSE), rich data payload inspection, and interactive approvals. We had to choose between a Single Page Application (SPA) built with Vite/React and a Server-Side Rendered (SSR) meta-framework like Next.js.

## Decision
We chose to build a **Single Page Application (SPA) using Vite + React + TypeScript** instead of Next.js.

## Rationale
1. **Streaming Performance**: The core functionality—consuming Server-Sent Events (SSE) token-by-token from the FastAPI backend—is heavily client-side. Next.js App Router caching layers and server actions add unnecessary complexity and latency to real-time streams compared to a direct browser-to-FastAPI connection.
2. **Backend Decoupling**: Milo already relies on a robust Python FastAPI backend for AI orchestration. Adding a Node.js server (Next.js) between the client and the Python backend violates our simplicity principle.
3. **PoC Deployment Velocity**: Vite provides near-instant HMR. The SPA can be trivially deployed to AWS S3/CloudFront or Amplify without provisioning SSR compute containers (ECS/Fargate/Lambda) for the frontend.
4. **State Management**: Complex client-side state (optimistic UI updates on approvals, streaming markdown chunks) is more straightforward in a pure React client context.

## Consequences
- We sacrifice SEO, which is entirely acceptable as the Milo Agent Workspace is a private, authenticated SaaS product, not a public-facing blog or marketing site.
- The initial bundle size might be larger, but the application is highly interactive, making the SPA tradeoff worthwhile.
