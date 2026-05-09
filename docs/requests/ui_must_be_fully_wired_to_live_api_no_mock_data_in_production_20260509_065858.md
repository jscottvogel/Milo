# UI Must Be Fully Wired to Live API — No Mock Data in Production

**Date:** 2026-05-09T06:58:58.200091
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
When the new UI (Next.js 15 on AWS Amplify) was introduced, connectivity to live program data was lost. The frontend is currently rendering mock or stub data instead of pulling from the live FastAPI backend and Milo tool chain. This must be resolved before Phase 7 (Web Frontend) can be considered complete. All UI components must connect to real, live API endpoints. No mock data, no hardcoded stubs, no placeholder responses are acceptable in any environment beyond local development.

## Acceptance Criteria
- [ ] Every UI component that displays program data fetches it from a live FastAPI endpoint — no mock data in staging or production.
- [ ] All 8 layers of the program hierarchy (objective → outcome → key result → initiative → project → workstream → milestone → task) render live data from the API.
- [ ] Risks, decisions, change requests, and stakeholders all load from live API responses.
- [ ] The Milo tool chain (email, calendar, work items, memory) is fully connected and responsive from the UI.
- [ ] A smoke test suite exists that hits each endpoint and confirms a non-mock response.
- [ ] Any component still using mock data is flagged with a // TODO: MOCK comment and tracked as a blocking issue before Phase 7 close.

## Technical Notes
Frontend: Next.js 15 deployed on AWS Amplify. Backend: FastAPI packaged in AWS Lambda, exposed via API Gateway. Auth: Confirm Cognito tokens are being passed correctly from Amplify → API Gateway → Lambda. Environment variables: Ensure NEXT_PUBLIC_API_BASE_URL points to the live API Gateway URL, not localhost or a mock server. CORS: Verify API Gateway CORS config allows requests from the Amplify domain. Use AWS CloudWatch logs to confirm Lambda is receiving and responding to real requests from the UI.
