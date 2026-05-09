# Stakeholder Identity & Cross-Tenant Profile System

**Date:** 2026-05-09T15:21:07.871750
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description

## Overview

Replace the current internal stakeholder CRM model with a self-service, invitation-driven stakeholder identity system. Stakeholders are first-class users with their own Cognito identity, a portable profile they own and maintain, and the ability to participate across multiple programs and multiple tenants — all from a single login.

This is a fundamental shift: **Milo does not own stakeholder data. The stakeholder does.**

---

## Core Concepts

### 1. Stakeholder Identity (Cognito)
- Every stakeholder gets a **dedicated Cognito User Pool account** in a shared `milo-stakeholders` pool (separate from the tenant admin pool).
- Stakeholders authenticate with their own email/password or federated IdP (Google, Microsoft).
- A stakeholder's Cognito `sub` (UUID) is their **global, immutable identity** — it is not scoped to any tenant.
- `tenant_id` is **NOT** stored as a Cognito attribute for stakeholders. This resolves the ADR-0003 conflict (see Technical Notes).

### 2. Stakeholder Profile (Self-Managed)
Upon first login (triggered by program invitation), the stakeholder completes a profile:
- Full name
- Title / Organization
- Preferred communication method: `email` | `sms` | `slack` | `teams` | `in-app`
- Communication frequency preference: `real-time` | `daily-digest` | `weekly-summary`
- Timezone
- Notification opt-ins (risk alerts, milestone updates, decision requests, action items)
- Bio / notes (optional)
- Avatar (optional)

Profile is stored in a **global `stakeholder_profiles` table** keyed by Cognito `sub`. It is not duplicated per tenant.

### 3. Program Membership (Tenant-Scoped Join Table)
Stakeholder participation in a program is managed via a `program_stakeholders` join table:
- `stakeholder_sub` (FK → global profile)
- `tenant_id`
- `program_id`
- `role` (sponsor, reviewer, contributor, observer, approver)
- `influence` (1–5)
- `interest` (1–5)
- `satisfaction` (1–5, optional, PM-managed)
- `invited_at`, `accepted_at`, `status` (pending / active / revoked)

A stakeholder can have rows in this table for **multiple tenants and multiple programs simultaneously**.

### 4. Invitation Flow
1. PM or Milo triggers an invitation: provides stakeholder email + role + program.
2. System checks if a global profile exists for that email.
   - **Exists:** Send a program-join notification with a deep link.
   - **New:** Send a Cognito invitation email (temporary password or magic link), then redirect to profile setup on first login.
3. Stakeholder accepts → `program_stakeholders` row status set to `active`.
4. Milo records the event in episodic memory.

### 5. Cross-Tenant Access
- A stakeholder's JWT (Cognito ID token) contains their global `sub` and a list of `tenant_memberships` (injected as a custom claim via a Pre-Token-Generation Lambda trigger).
- The API resolves which tenants/programs the stakeholder can access from the `program_stakeholders` table — never from the JWT alone.
- Tenant data isolation is enforced at the API layer: a stakeholder can only read data for programs they have an active membership row for.
- Tenants remain fully isolated from each other — a stakeholder seeing Program A (Tenant 1) and Program B (Tenant 2) never causes data from Tenant 1 to be visible in Tenant 2's context.

---

## Milo Integration
- Milo can trigger invitations autonomously via a new `stakeholder__invite` tool.
- Milo reads stakeholder communication preferences before sending any outreach — respects preferred channel and frequency.
- Milo's `work_item__update` for `stakeholder` entity type is updated to reference `stakeholder_sub` instead of storing a name string.
- Milo's morning briefing and trigger notifications are routed per stakeholder preference, not hardcoded to email.

---

## UI Requirements
- **Stakeholder Portal:** Lightweight, separate UI route (`/stakeholder`) — distinct from the PM dashboard. Mobile-friendly.
- **Profile Page:** Stakeholder edits their own profile. Changes propagate across all programs/tenants instantly.
- **My Programs:** List of all programs the stakeholder is active in, across all tenants, with RAG status indicators.
- **PM View:** Within the Program Detail page, the Stakeholders tab shows all active stakeholders with role, influence/interest matrix, satisfaction score, and last-contacted date.
- **Invitation Management:** PM can see pending invitations, resend, or revoke.


## Acceptance Criteria
- [ ] A stakeholder invited via email receives a Cognito invitation with a magic link or temporary password within 60 seconds of the invitation being triggered.
- [ ] A new stakeholder completing onboarding is prompted to fill out their full profile before being shown any program data.
- [ ] A returning stakeholder (existing Cognito sub) invited to a new program receives a program-join notification and is added to that program without being asked to re-register.
- [ ] A single stakeholder account can be active in programs across at least 2 different tenants simultaneously with a single login.
- [ ] The stakeholder JWT contains a `tenant_memberships` custom claim injected by the Pre-Token-Generation Lambda, listing all tenant/program pairs the stakeholder is active in.
- [ ] The API enforces that a stakeholder can only access data for programs where `program_stakeholders.status = active` — no exceptions.
- [ ] Data from Tenant A is never returned in any API response scoped to Tenant B, even when the same stakeholder sub is active in both.
- [ ] Stakeholder profile updates (e.g. preferred communication method) propagate to all programs and tenants within 1 minute.
- [ ] Milo respects the stakeholder's preferred communication method and frequency when sending any notification or outreach.
- [ ] The PM-facing Stakeholders tab displays role, influence, interest, satisfaction, and last-contacted date for all active stakeholders.
- [ ] PMs can invite, resend invitation to, and revoke access for stakeholders from within the program UI.
- [ ] Milo can trigger a stakeholder invitation autonomously via a `stakeholder__invite` tool call.
- [ ] The `program_stakeholders` join table correctly handles a stakeholder being revoked from one program without affecting their membership in any other program or tenant.
- [ ] The global `stakeholder_profiles` table has no `tenant_id` column — profile data is tenant-agnostic.
- [ ] All invitation and membership events are written to an audit log with timestamp, actor (PM or Milo), and action taken.

## Technical Notes

## ADR-0003 Amendment Required
The current ADR-0003 stores `tenant_id` as an immutable Cognito user attribute. This works for tenant admins and PMs but is incompatible with cross-tenant stakeholders. The amendment is:
- Tenant admins and PMs: retain `tenant_id` as a Cognito custom attribute in the **tenant pool**.
- Stakeholders: live in a **separate `milo-stakeholders` Cognito User Pool** with NO `tenant_id` attribute. Tenant membership is resolved exclusively from the `program_stakeholders` DB table.
- The Pre-Token-Generation Lambda for the stakeholder pool queries `program_stakeholders` and injects `tenant_memberships` as a custom claim array at token issuance time.

## AWS Architecture
- **Two Cognito User Pools:** `milo-tenant-pool` (existing, for PMs/admins) and `milo-stakeholder-pool` (new, for stakeholders).
- **App Clients:** Each pool has its own App Client. The frontend detects which pool to authenticate against based on the login entry point (PM dashboard vs. stakeholder portal).
- **Pre-Token-Generation Lambda:** Attached to `milo-stakeholder-pool`. On every token issuance, queries `program_stakeholders WHERE stakeholder_sub = $sub AND status = 'active'` and injects result as `custom:tenant_memberships` claim.
- **API Gateway Authorizer:** Updated to accept tokens from EITHER pool. Downstream resolvers check token issuer to determine if the caller is a PM or stakeholder and apply appropriate data scoping.
- **Global `stakeholder_profiles` table:** Single RDS/Aurora table, no `tenant_id` column. PK = Cognito `sub`.
- **`program_stakeholders` join table:** Contains `tenant_id` + `program_id` + `stakeholder_sub` + role/status fields. Composite PK = (`stakeholder_sub`, `tenant_id`, `program_id`).

## Invitation Email
- Use AWS SES for invitation and notification emails.
- For new stakeholders: Cognito AdminCreateUser with `MessageAction=SUPPRESS`, then send a custom SES email with a magic link (signed JWT, 72h expiry).
- For existing stakeholders: SES notification only — no Cognito action needed.

## Security Constraints
- Magic links must be single-use and expire after 72 hours.
- Revoked stakeholders must have their active sessions invalidated via Cognito GlobalSignOut scoped to the stakeholder pool.
- Never expose `tenant_id` values from other tenants in any stakeholder-facing API response.
- Rate-limit invitation endpoints to prevent enumeration attacks.

