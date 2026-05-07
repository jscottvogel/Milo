# Milo Platform — AI Code-Generation Build Prompts (PoC)

**Companion document to** `Milo_Platform_Build_Specification.docx` v1.3
**Target tool:** Google Antigravity (multi-agent IDE)
**Deployment mode:** PoC (per Section 6.7 of the spec)
**Primary AWS account:** `milo-poc` (single account, single AZ)

---

## How to use these prompts

1. Open Google Antigravity and load `Milo_Platform_Build_Specification.docx` v1.3 into the workspace as a reference document. Pin it so every agent run can consult it.
2. Run the phases **in order**. Each phase begins by reading the previous phase's deliverables; skipping or reordering will produce broken intermediate states.
3. For each phase, paste the entire prompt block for that phase into Antigravity. Use **Planner mode** first to let it produce a task breakdown, then **Builder mode** to execute. Review the generated plan before approving execution.
4. **Do not advance to the next phase until the current phase's "Verification gate" passes.** The gates exist to catch regressions early.
5. If a verification gate fails, paste the failure output back to the same Antigravity session and ask it to remediate; do not proceed with broken state.
6. After every phase, commit on a feature branch named `phase/<n>-<slug>` and open a pull request. The PR description must include the verification-gate output as a comment.

---

## §0 — Shared standards (binding for every phase)

Every phase prompt below enforces this section. If anything in a phase prompt conflicts with §0, §0 wins.

### Tooling pins

- **Python:** 3.12 (managed by `uv`)
- **Node.js:** 22 LTS (managed by `pnpm` via Corepack)
- **TypeScript:** 5.5
- **Postgres:** 16 (RDS db.t4g.micro for PoC, see Section 6.7 of spec)
- **AWS CDK:** v2 (TypeScript)
- **Test runners:** `pytest` (Python), `vitest` (TS unit), `playwright` (TS e2e)

### Code style

- **Python:** type hints on every function signature; `ruff` (lint), `black` (format), `mypy --strict`. No `Any` without an inline `# justified:` comment explaining why.
- **TypeScript:** `strict: true`, `noUncheckedIndexedAccess: true`, `eslint` + `@typescript-eslint`, `prettier`. No `any` without a `// justified:` comment.
- **No commented-out code** in the repo. Delete dead code; recover from git history if needed.
- **No `TODO` without a linked GitHub issue.** Format: `# TODO(#123): …` or `// TODO(#123): …`.
- **Errors are typed.** Python: custom exception classes per module. TypeScript: discriminated-union error types or `neverthrow` Result.
- **All public functions have docstrings/JSDoc** describing purpose, parameters, return value, and raised exceptions.
- **Functions exceed 40 lines or take >5 parameters → refactor.**
- **Cyclomatic complexity ≤ 10** per function (enforced by `ruff` and `eslint`).

### Test requirements

- **Unit tests:** every public function in `packages/` and `apps/api/app/` has a unit test. Coverage gate: **≥85% line, ≥75% branch.**
- **Integration tests:** every API endpoint has an integration test that exercises the real database and a mocked LLM. Coverage gate: **100% of endpoints.**
- **End-to-end tests:** every primary user flow (signup, send message, approve action, connect Gmail) has a Playwright test.
- **Eval scenarios:** agent behavior is tested with at least 20 YAML scenario files by Phase 4 and 50 by Phase 10. See Section 13.4 of spec.
- **No flaky tests tolerated.** A test that fails intermittently is treated as a failing test until fixed.

### Documentation requirements

- **`README.md` at repo root** with: what Milo is (one paragraph), prerequisites, quick start, link to the build spec, link to this prompts document, contributing guide, license.
- **`README.md` per package and per app** describing its responsibility, public API, how to run its tests.
- **ADRs (Architecture Decision Records)** in `docs/adr/` for any non-obvious decision. Format: MADR template. The choice of pgvector over OpenSearch (already documented in the spec) gets ADR-0001.
- **OpenAPI spec** auto-generated from FastAPI; published as `apps/api/openapi.json`; consumed by the web app via `openapi-typescript` to generate client types.
- **Inline comments only when *why*, never *what*.** The code shows what; comments must explain why.

### CI requirements

- **GitHub Actions** with these required checks: `lint`, `typecheck`, `test-unit`, `test-integration`, `cdk-synth`, `security-scan` (Snyk + Bandit + Semgrep), `eval-subset` (10 scenarios on PR, full 50 on `main`).
- **GitHub OIDC** federates into AWS; no long-lived AWS access keys in Actions secrets.
- **Branch protection on `main`:** require PR review, all checks green, linear history, signed commits.
- **Conventional Commits** (`feat:`, `fix:`, `chore:`, etc.). Enforced by commitlint.

### Repository layout (binding)

```
milo/
├── apps/
│   ├── web/                  Next.js 15 App Router; Amplify-deployable
│   └── api/                  FastAPI app; Lambda Function URL deployable in PoC
├── packages/
│   ├── agent/                LangGraph runtime, tool registry, prompts
│   ├── db/                   SQLAlchemy 2.0 models, Alembic migrations
│   ├── shared-schemas/       Pydantic models exported as JSON Schema
│   ├── shared-types/         TypeScript types generated from shared-schemas
│   └── cdk/                  AWS CDK app
├── services/
│   └── mcp/
│       ├── _template/        Reference implementation of an MCP server
│       └── gmail/            First integration (Phase 8)
├── tools/
│   ├── eval/                 Eval harness + scenarios (.yaml)
│   ├── seed/                 Seed-data scripts for dev
│   └── scripts/              Misc dev scripts
├── docs/
│   ├── adr/
│   ├── runbooks/
│   └── diagrams/
├── .github/workflows/
├── pyproject.toml            uv workspace root
├── pnpm-workspace.yaml
├── package.json
├── Makefile                  Common dev tasks
├── .pre-commit-config.yaml
├── .editorconfig
└── README.md
```

### Definition of Done (every phase, every PR)

A phase is **done** only when **all** of the following are true:

1. All code passes `make lint typecheck test cdk-synth` locally and in CI.
2. New tests exist and the coverage gate passes.
3. New endpoints have an integration test.
4. New user flows have a Playwright test.
5. The `README.md` in any new/changed package is updated.
6. ADRs are written for any non-obvious decision.
7. The phase's specific **Verification gate** (described in each phase prompt) passes and its output is attached to the PR.
8. The PoC infrastructure cost has not increased above the budget stated in Section 6.7 of the spec (~$25–40/month). If a change pushes cost up, it must be justified in the PR description with a forecast.

---

## Phase 0 — Repository scaffolding, tooling, CI bootstrap

**Goal:** Stand up an empty-but-complete monorepo that any subsequent phase can extend. No application logic — just structure, tooling, and a green CI run.

**Prerequisites:** None. This is the first phase.

**Prompt to paste into Antigravity:**

> You are implementing Phase 0 of the Milo platform PoC build, per the standards in §0 of `Milo_Antigravity_Build_Prompts.md` and the architecture in Section 6.7 of `Milo_Platform_Build_Specification.docx` (PoC mode).
>
> **Deliverables for this phase:**
>
> 1. Initialize a Git repository at the workspace root with `main` as the default branch and a `.gitignore` covering Python, Node, TypeScript, AWS CDK, and macOS/Windows artifacts.
> 2. Create the directory tree exactly as specified in §0 "Repository layout."
> 3. Set up `uv` workspaces in `pyproject.toml` listing `apps/api`, `packages/agent`, `packages/db`, `packages/shared-schemas`, and `services/mcp/_template` as members. Pin Python 3.12.
> 4. Set up `pnpm` workspaces in `pnpm-workspace.yaml` listing `apps/web`, `packages/shared-types`, and `packages/cdk`. Pin Node 22.
> 5. Configure `ruff` (lint), `black` (format, line length 100), `mypy` (strict), `bandit` for the Python side, and `eslint` (with `@typescript-eslint`), `prettier`, `commitlint` for the TS side. Configs go in the repo root.
> 6. Add a `Makefile` with these targets: `setup`, `lint`, `typecheck`, `test`, `test-unit`, `test-integration`, `test-e2e`, `cdk-synth`, `clean`, `format`, `eval`, `dev`, `dev-api`, `dev-web`. Each target must work even when called in isolation.
> 7. Add `.pre-commit-config.yaml` running ruff, black, mypy, eslint, prettier, detect-secrets, and a license-header check on commit.
> 8. Add a placeholder `README.md` at the repo root with the structure required by §0 (Documentation requirements). Use the spec doc and prompts doc as references in the README links.
> 9. Add `LICENSE` (copyright Milo Platform — placeholder; tag for follow-up).
> 10. Create `docs/adr/0001-pgvector-over-opensearch.md` documenting the decision per Section 6.2 of the spec. Use the MADR template.
> 11. Set up `.github/workflows/ci.yml` with these jobs: `lint`, `typecheck`, `test-unit`, `cdk-synth`, `security-scan`. They run on every PR and on push to `main`. Use GitHub OIDC for any AWS calls (placeholder role ARNs documented in the workflow file).
> 12. Add `.github/CODEOWNERS` with a single placeholder owner the team can replace.
> 13. Add a `CONTRIBUTING.md` describing the branch-naming convention (`phase/<n>-<slug>`), the conventional-commits requirement, and the PR template requirement.
> 14. Add `.github/pull_request_template.md` requiring: phase number, summary, verification-gate output paste-in, infra-cost impact statement, screenshots if UI changed.
>
> **Code requirements:**
>
> - Every config file is committed; nothing is "set up only on the dev's machine."
> - All paths use forward slashes; the repo must work on Windows, macOS, and Linux.
> - The CI workflow must complete in under 4 minutes on an empty repo.
>
> **Verification gate (must all pass before the PR can be merged):**
>
> Run these commands; each must exit zero with no warnings:
>
> ```bash
> make setup       # installs uv + pnpm + python and node deps
> make lint        # ruff + eslint
> make typecheck   # mypy --strict + tsc --noEmit
> make test-unit   # pytest -q + vitest run (zero tests is acceptable in Phase 0)
> make cdk-synth   # cdk synth on the empty CDK app
> ```
>
> Then push the branch and confirm the GitHub Actions run is green. Paste the green-run URL into the PR description.
>
> **Phase 0 is NOT complete until** the CI run is green on a PR opened against `main`. Do not proceed to Phase 1 until this is true.

---

## Phase 1 — Database and data model

**Goal:** Provision the RDS PoC database via CDK, implement every entity from Section 7 of the spec as SQLAlchemy 2.0 models, write Alembic migrations, and enforce row-level security.

**Prerequisites:** Phase 0 merged.

**Prompt to paste into Antigravity:**

> You are implementing Phase 1 of the Milo platform PoC. Read Section 7 (Data Model) of `Milo_Platform_Build_Specification.docx` v1.3 and Appendix C (Sample Postgres DDL). Read Section 6.7 (PoC mode database choice) of the same document. Apply §0 standards.
>
> **Deliverables for this phase:**
>
> 1. In `packages/cdk`, define a `DatabaseStack` that provisions:
>    - A VPC (`mode=poc` in the constructs flag): default-VPC equivalent — single AZ, public subnets only, no NAT Gateway, security group permitting only inbound on 5432 from a CIDR allowlist (developer IPs and Lambda subnet).
>    - One `aws-cdk-lib/aws-rds.DatabaseInstance` of class `db.t4g.micro`, single-AZ, storage 20 GB gp3, encrypted with an AWS-managed KMS key, automated daily backups retained 7 days, deletion protection ON.
>    - The Postgres `pgvector` extension is enabled in a custom parameter group.
>    - Master credentials in AWS Secrets Manager with rotation NOT enabled in PoC mode (defer to Production mode per Section 6.7).
> 2. In `packages/db`, implement SQLAlchemy 2.0 declarative models for every table named in spec Section 7.2 through 7.7: `tenants`, `users`, `memberships`, `milos`, `programs`, `milestones`, `tasks`, `stakeholders`, `risks`, `decisions`, `commitments`, `threads`, `messages`, `tool_calls`, `approvals`, `agent_runs`, `memory_chunks`, `memory_facts`, `embeddings_jobs`, `integrations`, `oauth_tokens`, `integration_events`, `subscriptions`, `usage_meters`, `invoices_cache`. Use `Mapped`/`mapped_column` syntax (SQLAlchemy 2.0 native). Type everything.
> 3. Set up Alembic in `packages/db/alembic/`. Generate the initial migration that creates every table, every index named in spec Section 7.8, and every Row-Level Security policy. Apply the policy template `USING (tenant_id = current_setting('app.tenant_id')::uuid)` to every tenant-owned table. The migration must include `CREATE EXTENSION IF NOT EXISTS pgvector` and `CREATE EXTENSION IF NOT EXISTS pgcrypto`.
> 4. Implement a `db_session` context manager that opens a session, sets `app.tenant_id` from a passed-in tenant UUID via `SET LOCAL`, and yields. This is the canonical entry point — no module is allowed to create raw sessions outside this helper.
> 5. Add `tools/seed/seed_dev.py` that creates one demo tenant, one demo user, and one demo program with one milestone and three tasks for use in local dev.
> 6. Unit tests in `packages/db/tests/`:
>    - One test per model that asserts table creation, primary-key uniqueness, and that all NOT NULL columns are enforced.
>    - One test that confirms the `db_session` helper sets `app.tenant_id` correctly and that queries from a different tenant ID return zero rows (RLS enforcement).
>    - One test per index/constraint named in Section 7.8.
> 7. Integration tests in `packages/db/tests/integration/` against a real Postgres (use `testcontainers-python`):
>    - Cross-tenant isolation: insert rows for tenant A, query as tenant B, assert empty.
>    - Migration round-trip: apply all migrations, downgrade to base, re-upgrade — schema must match.
>    - HNSW index sanity: insert 1000 random embeddings, run a top-10 ANN query, assert latency < 50ms.
> 8. Update `docs/adr/` with `0002-rls-tenant-isolation.md` documenting the chosen RLS approach.
> 9. Update `packages/db/README.md` describing how to run migrations locally, how the `db_session` helper works, and how to add a new table (link to ADR-0002).
>
> **Code requirements:**
>
> - All foreign keys have `ON DELETE CASCADE` where the referenced row owns the data (per spec).
> - Every datetime column is `timestamptz` and stored in UTC.
> - Money columns (if any in this phase) are `numeric(12,2)`.
> - No string `enum` columns without a `CHECK` constraint enumerating values, OR a Postgres ENUM type — pick CHECK (more migration-friendly).
>
> **Verification gate:**
>
> ```bash
> make lint typecheck
> cd packages/db && uv run alembic upgrade head    # against testcontainer
> uv run pytest -q packages/db                     # unit tests
> uv run pytest -q packages/db/tests/integration   # integration tests
> cd packages/cdk && pnpm cdk synth -c mode=poc    # CDK synth must succeed
> ```
>
> Coverage must be ≥85% line / ≥75% branch in `packages/db`.
>
> Do not deploy the `DatabaseStack` to AWS yet. CDK `synth` only.

---

## Phase 2 — Identity, multi-tenancy, and base API

**Goal:** Stand up Cognito, the FastAPI app skeleton, and tenant-context propagation so every subsequent phase can rely on authenticated requests with a verified `tenant_id`.

**Prerequisites:** Phase 1 merged.

**Prompt to paste into Antigravity:**

> You are implementing Phase 2 of the Milo platform PoC. Read Section 6.3 (Multi-tenancy), Section 8 (API Specification), and Section 12 (Security) of `Milo_Platform_Build_Specification.docx` v1.3. Apply §0 standards.
>
> **Deliverables for this phase:**
>
> 1. In `packages/cdk`, add an `IdentityStack` that provisions an Amazon Cognito User Pool with:
>    - Email + magic link sign-in primary; OAuth2 with Google and Microsoft as secondary identity providers (configured but disabled until OAuth client IDs are supplied via SSM).
>    - Custom attributes: `tenant_id` (immutable, string, max 36), `role` (mutable, string, max 16).
>    - MFA optional in PoC mode (required in prod per spec).
>    - Hosted UI domain: `milo-poc-auth` (placeholder; document how to change).
>    - One App Client for the web app, public, no client secret.
> 2. In `apps/api`, scaffold a FastAPI app with:
>    - `app/main.py` exposing the FastAPI instance.
>    - `app/config.py` using `pydantic-settings` to load environment variables, with explicit fields for `DATABASE_URL`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `AWS_REGION`, `LOG_LEVEL`.
>    - `app/middleware/auth.py` that verifies the Cognito JWT (using `python-jose` or `pyjwt[cryptography]` with JWKS caching), extracts `sub`, `email`, `custom:tenant_id`, `custom:role`, and attaches a typed `RequestContext` to `request.state`.
>    - `app/middleware/tenant_context.py` that, after auth, sets `app.tenant_id` on the database session for the duration of the request via the `db_session` helper from Phase 1.
>    - `app/middleware/logging.py` that emits structured JSON logs with mandatory fields per spec Section 13.1 (`tenant_id`, `user_id`, `request_id`, `latency_ms`, `level`, `message`).
>    - `app/middleware/error_handler.py` returning the spec Section 8.6 error model `{error: {code, message, request_id, details?}}`.
> 3. Implement these endpoints from spec Section 8.2:
>    - `GET /v1/health` (public, no auth)
>    - `GET /v1/me` (authed; returns user + memberships)
>    - `POST /v1/tenants` (authed; first-tenant signup; sets the `custom:tenant_id` on the Cognito user via Admin API)
>    - `GET /v1/tenants/:id` (authed, owner/admin only)
>    - The remaining endpoints from Section 8.2 are stubbed to return `501 NOT_IMPLEMENTED` and tagged with the phase number that will implement them. This makes future phases discoverable in OpenAPI.
> 4. Generate `apps/api/openapi.json` and a publish step that copies it into `packages/shared-types/openapi.json` so the web app can consume types via `openapi-typescript` in a later phase.
> 5. Add a `local` runtime: `make dev-api` runs the API on `localhost:8000` against a local Postgres (via `docker compose up postgres` for dev only — not deployed) with seeded data from Phase 1.
> 6. Unit tests in `apps/api/tests/unit/`:
>    - JWT verification: valid token, expired token, wrong issuer, wrong audience, missing tenant_id claim — five separate tests.
>    - Tenant-context middleware: verify `app.tenant_id` is set before route handler runs and unset after.
>    - Error handler: each `HTTPException` subtype maps to the documented error code.
> 7. Integration tests in `apps/api/tests/integration/`:
>    - `GET /v1/health` returns 200.
>    - `GET /v1/me` returns 401 without a token.
>    - `GET /v1/me` returns 200 with a valid token signed by a local JWKS fixture.
>    - `POST /v1/tenants` creates a tenant and updates the Cognito user (use `moto` to mock Cognito).
>    - `GET /v1/tenants/:id` enforces RLS — a user from tenant B cannot read tenant A.
> 8. Update `apps/api/README.md` with: how to run the API locally, how to obtain a dev JWT, how to add a new endpoint (link to a checklist), how the auth/tenant middleware chain works.
> 9. Add `docs/adr/0003-cognito-tenant-claim.md` documenting the choice of storing `tenant_id` on the Cognito user vs in a separate table.
>
> **Code requirements:**
>
> - The auth middleware **never** trusts request headers other than the JWT for tenant_id. Even an admin user changing tenants must re-authenticate.
> - There is **no code path** in the API that queries the database without `app.tenant_id` set. Add a SQLAlchemy event listener that raises if a query is issued without the setting.
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> cd apps/api && uv run pytest -q --cov=app --cov-fail-under=85
> cd packages/cdk && pnpm cdk synth -c mode=poc
> # Smoke test:
> make dev-api &
> curl -f http://localhost:8000/v1/health
> # Authed smoke test using a dev JWT:
> python tools/scripts/issue_dev_jwt.py | xargs -I{} curl -f -H "Authorization: Bearer {}" http://localhost:8000/v1/me
> ```
>
> The OpenAPI document at `http://localhost:8000/openapi.json` must list every endpoint from spec Section 8.2 (implemented or stubbed).

---

## Phase 3 — Agent runtime core (LangGraph + Bedrock)

**Goal:** Build the LangGraph state machine for Milo's agent loop, wire it to Amazon Bedrock for Claude inference, implement memory layers, and prove end-to-end with a no-tools "echo" scenario.

**Prerequisites:** Phase 2 merged.

**Prompt to paste into Antigravity:**

> You are implementing Phase 3 of the Milo platform PoC. Read Section 5 (Agent Design), Appendix A (Sample Milo System Prompt), and Section 6.6 (Real-time / streaming) of `Milo_Platform_Build_Specification.docx` v1.3. Apply §0 standards.
>
> **Deliverables for this phase:**
>
> 1. In `packages/agent`, implement the LangGraph state machine described in spec Section 5.1: nodes `Perceive`, `Plan`, `Act`, `Observe`, `Reflect`. Use `langgraph` 0.2+. Define the agent state as a typed Pydantic `AgentState` with fields for thread, working memory, last tool call, last tool result, pending approvals, and finish reason.
> 2. Implement the system-prompt assembly described in spec Section 5.2 — five layers concatenated at runtime:
>    - Layer 1: immutable identity (load from `prompts/identity.md`).
>    - Layer 2: tenant persona pack (`trades` or `sme`) loaded from `prompts/packs/<pack>.md`.
>    - Layer 3: program context summary (placeholder for now; populated in later phase).
>    - Layer 4: memory retrieval insertions (placeholder).
>    - Layer 5: tool catalog (start empty in Phase 3; tools land in Phase 4).
>    Layers 1–3 are prompt-cached using Bedrock prompt caching breakpoints.
> 3. Implement the Bedrock client wrapper at `packages/agent/agent/llm/bedrock.py`:
>    - One method `invoke_with_streaming(messages, system, tools, model)` returning an async iterator over events (token, tool_use, tool_use_input_delta, message_stop).
>    - Routes `model='primary'` to Claude Sonnet 4.6 on Bedrock and `model='cheap'` to Haiku 4.5. Model IDs come from config; never hardcoded.
>    - Tracks input/output tokens per call and emits a `LLMUsage` record for observability.
>    - Exponential-backoff retry on Bedrock throttling errors.
>    - Optional fallback: if `BEDROCK_FALLBACK_TO_ANTHROPIC=true`, on `ModelNotReadyException` fall through to direct Anthropic SDK using a key from Secrets Manager.
> 4. Implement the four memory layers from spec Section 5.4 in `packages/agent/agent/memory/`:
>    - `working.py`: per-turn message buffer; bounded at 80K tokens; older turns summarized into thread memory automatically.
>    - `thread.py`: rolling summary + last 20 messages; reads from / writes to the `threads.summary` and `messages` tables.
>    - `program.py`: structured fetch from the `programs`, `milestones`, `tasks`, `risks`, `decisions`, `commitments` tables — never via vector search (per spec).
>    - `episodic.py`: top-k vector search against `memory_chunks` using pgvector; embedding via Titan Text Embeddings v2 on Bedrock.
>    - `semantic.py`: key-value lookup against `memory_facts`.
> 5. Implement an `AgentRunner` class with method `run_turn(thread_id, user_message)` that:
>    - Loads thread/program/memory context.
>    - Assembles the system prompt via the layer mechanism.
>    - Streams a Bedrock response.
>    - Persists the user message and assistant message into `messages`.
>    - Updates `agent_runs` with cost and turn count.
>    - Yields tokens as an async iterator suitable for SSE forwarding.
> 6. Add a stub tool registry that is empty in Phase 3 — Phase 4 fills it. Define the tool interface as a Pydantic-validated `Tool` protocol with `name`, `input_schema`, `output_schema`, `mutates` (bool), `requires_approval` (bool), and `invoke(input, context) -> output` method.
> 7. Implement the `<untrusted>` content wrapper described in spec Section 5.5 — every tool result that contains third-party content is wrapped before being returned to the model.
> 8. Wire the API endpoint `POST /v1/threads/:id/messages` (was stubbed in Phase 2) to the `AgentRunner` and emit SSE events on `GET /v1/threads/:id/turns/stream` per spec Section 8.3 (token, tool_call, tool_result, approval_request, done events).
> 9. Eval harness scaffold in `tools/eval/`:
>    - `runner.py` that takes a YAML scenario, instantiates a sandboxed tenant, runs the agent against scripted user messages, and asserts on tools called, artifacts produced, and approval queue contents.
>    - 5 starter scenarios in `tools/eval/scenarios/`: a "Hello, Milo" smoke test, an empty-program greeting, a multi-turn dialogue, a context-load test (loads program memory), and a Bedrock cost-cap test.
> 10. Unit tests covering: prompt assembly, layer caching keys, Bedrock client error paths, memory token budgets, working-memory summarization triggers.
> 11. Integration tests covering: a full end-to-end agent turn with Bedrock mocked (use `botocore.stub.Stubber`), persistence into the database, SSE event ordering.
> 12. ADR `0004-langgraph-vs-custom-loop.md` documenting why we use LangGraph.
> 13. ADR `0005-titan-embeddings-vs-voyage.md` documenting the embeddings choice.
>
> **Code requirements:**
>
> - The agent **must not** ever produce a response that bypasses the layer mechanism. Add a runtime assertion that the system prompt is assembled via the layer builder.
> - The agent **must** record every Bedrock call (tokens, model, duration, cost in USD computed from the published Bedrock rates) into `agent_runs`. No Bedrock call goes unmetered.
> - The agent **must** halt and emit `handoff.human` when (a) it has executed >20 tool calls in one turn, or (b) cumulative cost in one turn exceeds $0.50 (configurable per tenant).
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> uv run pytest -q packages/agent --cov=agent --cov-fail-under=85
> uv run python tools/eval/runner.py --all-starters
> # All 5 starter scenarios must pass.
> # Manual SSE smoke test:
> make dev-api &
> python tools/scripts/agent_smoke.py "Hello, who are you?"
> # Expected: streamed response identifying itself as Milo, finished with done event, cost <$0.01.
> ```
>
> Phase 3 is complete only when the SSE smoke test produces a fluent response and `agent_runs` has a row with non-null `cost_usd`.

---

## Phase 4 — Tool catalog (MVP set)

**Goal:** Implement the Phase-1 tools from spec Section 5.3 so Milo can read memory, read programs, draft emails, read calendars, and read/write storage. Mutations are queued (Phase 5 wires the queue UI; the back-end mechanism lands here).

**Prerequisites:** Phase 3 merged.

**Prompt to paste into Antigravity:**

> You are implementing Phase 4. Read spec Section 5.3 (Tool catalog) and Appendix B (Sample Tool Schemas). Apply §0 standards.
>
> **Deliverables:**
>
> 1. Implement these tools, each as a class implementing the `Tool` protocol from Phase 3:
>    - `memory.search` — top-k against `memory_chunks` with metadata filters.
>    - `memory.write` — append a chunk; auto-embed via Titan; never approval-gated.
>    - `program.read` — return structured program data.
>    - `program.update` — patch program/milestone/task/risk/decision; non-financial fields auto, financial fields gated.
>    - `email.draft` — produce an email body and subject; persists a draft row, returns draft ID; never approval-gated.
>    - `calendar.read` — read-only against the local DB cache (Gmail/GCal sync lands in Phase 8).
>    - `storage.read` / `storage.write` — S3 GetObject / PutObject scoped by tenant prefix; writes to shared folders gated.
>    - `web.search` — tavily-style search via a wrapper; the actual provider can be `tavily-python` (paid) or DuckDuckGo (free) — pick free for PoC.
>    - `web.fetch` — HTTP GET with redirect-cap, size-cap, content-type allowlist.
>    - `handoff.human` — emit an event into the approval queue tagged `escalation`.
> 2. Each tool has:
>    - A Pydantic input schema and output schema.
>    - A unit test for happy path, validation failure, and per-tool error case.
>    - A docstring rendering as part of the tool catalog passed to the LLM.
> 3. Register all tools in a `tool_registry` accessed by the `AgentRunner`. Tools are discovered automatically by inspecting `packages/agent/agent/tools/` package.
> 4. Implement the **approval gate** primitive in `packages/agent/agent/approvals.py`:
>    - When the LLM calls a tool with `requires_approval=True`, the runner enqueues an `approvals` row, emits an `approval_request` SSE event, and pauses the run.
>    - The run resumes when the approval is approved (apply original input), edited (apply edited input), or rejected (skip the tool, return a `cancelled_by_user` result to the model).
> 5. Add 10 new eval scenarios that exercise each tool at least once.
> 6. Update `apps/api` with the `GET /v1/approvals` and `POST /v1/approvals/:id/decide` endpoints from spec Section 8.2.
> 7. Update web-bound types in `packages/shared-types/` so the frontend can render tool calls and approvals.
> 8. ADR `0006-mcp-protocol-internal-vs-external.md` describing why Phase 4 tools are in-process Python rather than separate MCP servers (per spec Section 6.7 PoC mode).
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> uv run pytest -q packages/agent --cov-fail-under=85
> uv run python tools/eval/runner.py --all
> # All 15 scenarios must pass.
> # Manual: run a scenario that exercises a mutating tool and confirm the approval row appears in the DB and the SSE stream emits approval_request.
> ```

---

## Phase 5 — Approval queue UX, autonomy levels, escalation

**Goal:** Make approvals a first-class user experience — list, decide, edit, expire — and wire the per-tool-class autonomy slider from spec Section 5.7.

**Prerequisites:** Phase 4 merged.

**Prompt to paste into Antigravity:**

> You are implementing Phase 5. Read spec Section 5.7 (Human-in-the-loop policies) and Section 10.4 (Approval queue). Apply §0 standards.
>
> **Deliverables:**
>
> 1. Implement the autonomy-level mechanism: each `milos.autonomy_levels` is a `jsonb` map of tool-class → level (`draft|copilot|auto`). The runner consults this before queuing — `auto` level skips the queue. `auto` is locked off for `sms.send`, `esign.send`, and `quickbooks.write` per spec.
> 2. Implement approval expiration (default 24h) via an EventBridge rule that nightly transitions stale `pending` rows to `expired`.
> 3. API additions: `PATCH /v1/milos/:id/autonomy` to update autonomy levels (owner/admin role only).
> 4. Eval scenarios: 5 new scenarios covering approve, reject, edit, autonomy-raise, and expiration.
> 5. Notifications: when an approval is queued, emit a record into a `notifications` table (a small new table — add migration). The web app polls this in Phase 7.
> 6. Web frontend work is deferred to Phase 7; in this phase just expose API + queue mechanics.
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> uv run pytest -q --cov-fail-under=85
> uv run python tools/eval/runner.py --tag approvals
> ```

---

## Phase 6 — API completion, Lambda packaging, SSE wiring

**Goal:** Finish every REST endpoint listed in spec Section 8.2, package the API and agent runtime as a single Lambda Function URL with response streaming (PoC mode), and deploy the first end-to-end stack to `milo-poc`.

**Prerequisites:** Phase 5 merged.

**Prompt to paste into Antigravity:**

> You are implementing Phase 6. Read spec Section 6.7 (PoC mode API + agent runtime collapsed to a single Lambda Function URL), Section 8 (API spec), and Section 14 (Deployment). Apply §0 standards.
>
> **Deliverables:**
>
> 1. Implement every remaining `501` endpoint from Phase 2. Each endpoint has a unit + integration test.
> 2. Package `apps/api` as a Lambda function using `mangum` (ASGI → Lambda adapter). The handler entry is `apps/api/lambda_handler.py`.
> 3. In `packages/cdk`, add an `ApiStack` that, in `mode=poc`:
>    - Builds the Lambda from a Docker image (Lambda container image — required because we need uvicorn dependencies).
>    - Configures a Lambda Function URL with `InvokeMode=RESPONSE_STREAM` (this is what makes SSE work).
>    - Memory 1024 MB, timeout 900s (15 min), reserved concurrency 5 (PoC cost guardrail).
>    - IAM execution role with least-privilege access to: Bedrock InvokeModel + InvokeModelWithResponseStream, RDS connection via Secrets Manager, S3 read/write on the tenant-prefix path, SQS send/receive for the briefing queue, Parameter Store read for OAuth tokens.
>    - Public Function URL (auth handled in-app via Cognito JWT).
> 4. Add `WebStack` placeholder (real frontend lands in Phase 7).
> 5. CI: add an integration-test job that deploys the stack into a CI-only AWS account (or LocalStack), runs the integration suite against the deployed Function URL, and tears down. Mark optional in PoC if cost-prohibitive.
> 6. ADR `0007-lambda-function-url-vs-apigw-for-streaming.md` per the spec rationale.
> 7. Runbook `docs/runbooks/deploy-poc.md` with step-by-step instructions to deploy the PoC stack from a fresh AWS account. Include AWS Activate credit application instructions.
> 8. Cost-forecast doc `docs/cost-forecast-poc.md` — an Excel-style table per spec Section 6.7 showing expected monthly cost line-by-line.
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> uv run pytest -q --cov-fail-under=85
> cd packages/cdk && pnpm cdk diff -c mode=poc
> cd packages/cdk && pnpm cdk deploy -c mode=poc --require-approval never
> # Smoke against the deployed Function URL:
> tools/scripts/post_smoke.sh "$FUNCTION_URL"
> # Expected: 200 on /v1/health, JWT-protected endpoints respond correctly, SSE stream produces tokens.
> ```

---

## Phase 7 — Web frontend (Next.js 15 on Amplify)

**Goal:** Ship the customer-facing web app with the conversation UI, approval queue, integration management, and settings.

**Prerequisites:** Phase 6 deployed.

**Prompt to paste into Antigravity:**

> You are implementing Phase 7. Read spec Section 6.2 (frontend stack) and Section 10 (Onboarding & Core User Flows). Apply §0 standards.
>
> **Deliverables:**
>
> 1. In `apps/web`, scaffold a Next.js 15 App Router app with TypeScript strict mode, Tailwind v4, shadcn/ui, TanStack Query.
> 2. Use `openapi-typescript` against `packages/shared-types/openapi.json` to generate a typed API client. Wrap it in a TanStack Query layer at `apps/web/lib/api.ts`.
> 3. Cognito integration via `aws-amplify` JS library for sign-up, sign-in, magic-link, and federated providers (configured but disabled in PoC).
> 4. Build these pages and components:
>    - `/` — marketing landing (placeholder; can be 1-screen).
>    - `/signup` — Cognito sign-up + tenant creation wizard.
>    - `/app` — authenticated shell with left rail (Programs, Approvals, Settings) and main panel.
>    - `/app/programs` — list and detail.
>    - `/app/programs/:id/threads/:tid` — conversation UI with token-streaming via Vercel AI SDK on the client; renders tool-call cards and approval cards inline.
>    - `/app/approvals` — approval queue with Approve / Reject / Edit (inline editor).
>    - `/app/settings/integrations` — list of integrations with Connect / Disconnect (Connect is wired in Phase 8).
>    - `/app/settings/autonomy` — per-tool-class autonomy slider.
>    - `/app/billing` — embed Stripe Customer Portal (Phase 9 wires this).
> 5. Use `next-themes` for light/dark; ship with a default Milo theme (steel blue + warm grey).
> 6. Implement client-side error boundary + Sentry init (free tier).
> 7. Configure `apps/web/amplify.yml` for AWS Amplify Hosting builds. Set up custom domain instructions in `docs/runbooks/web-domain-setup.md`.
> 8. Playwright tests in `apps/web/tests/e2e/` for: signup, send a message, see streaming tokens, approve a queued action, edit and approve a queued action, reject an action, change autonomy level.
> 9. Lighthouse perf gate: target 90+ on Performance and Accessibility on the conversation page (run as part of CI).
> 10. Update root `README.md` with screenshots.
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> cd apps/web && pnpm test --coverage  # vitest unit
> cd apps/web && pnpm test:e2e         # playwright against deployed PoC stack
> cd apps/web && pnpm lighthouse:ci    # perf + a11y gate
> # Manual: full-loop manual test from sign-up to first approved action.
> ```

---

## Phase 8 — First integration (Gmail) + MCP framework

**Goal:** Build the MCP server framework as an in-process pattern, implement the Gmail MCP, complete the OAuth2 PKCE flow, and prove a real-world action: Milo reads inbox, drafts a reply, queues for approval, sends.

**Prerequisites:** Phase 7 deployed.

**Prompt to paste into Antigravity:**

> You are implementing Phase 8. Read spec Section 9 (Integrations), Section 9.3 (Gmail detail), and Section 11.5 (OAuth secrets handling). Apply §0 standards.
>
> **Deliverables:**
>
> 1. In `services/mcp/_template/`, build a reference MCP server scaffold: a Pydantic-validated `MCPServer` base class with `connect`, `refresh_tokens`, `tools[]`, and a CLI for local testing.
> 2. In `services/mcp/gmail/`, implement the Gmail MCP per spec Section 9.3. Tools: `list_threads`, `read_thread`, `draft_email`, `send_email` (queued).
> 3. OAuth2 PKCE flow in the API: `POST /v1/integrations/gmail/connect` returns `authorize_url`; `GET /v1/integrations/oauth/callback` completes the flow, encrypts tokens with the per-tenant DEK, stores in Parameter Store at path `/milo/tenants/<tenant_id>/integrations/gmail`.
> 4. In PoC mode, Gmail MCP runs as an in-process Python module imported by the agent runtime Lambda. Document the migration path to a separate Fargate service for Production mode in the MCP `README.md`.
> 5. Inbox-poll background job: EventBridge Scheduler triggers a Lambda every 5 minutes (PoC frequency; spec says 2 minutes — relaxed for cost). Fetches new messages, runs Haiku-based triage, persists to DB, and creates `commitments` rows for any "I will…" detected.
> 6. Eval scenarios: 5 new scenarios covering inbox triage, drafting, approval, send, and an error path (revoked OAuth token).
> 7. Web UI: complete the `Settings → Integrations → Gmail` flow with Connect → OAuth dance → Connected state.
> 8. Documentation: `services/mcp/gmail/README.md` covering OAuth scopes, rate limits per spec, error handling, and how to add the next integration following the template.
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> uv run pytest -q --cov-fail-under=85
> uv run python tools/eval/runner.py --tag gmail
> # Manual full loop: connect a test Gmail account; verify inbox is read; ask Milo to draft a reply; approve; verify email is in Sent folder.
> ```

---

## Phase 9 — Billing, onboarding, founding-customer promo

**Goal:** Ship Stripe billing per spec Section 11, complete the signup wizard, and turn on the founding-customer promo.

**Prerequisites:** Phase 8 deployed.

**Prompt to paste into Antigravity:**

> You are implementing Phase 9. Read spec Section 11 (Billing & Pricing) — pricing v1.3 with Solo at $50/mo, Team at $150/mo flat, Business deferred until v1.1, Enterprise custom. Apply §0 standards.
>
> **Deliverables:**
>
> 1. Stripe products and prices via the Stripe CLI provisioning script `tools/scripts/stripe_setup.sh`. Products: `milo-solo-monthly`, `milo-solo-annual`, `milo-team-monthly`, `milo-team-annual`, `milo-overage-input-tokens`, `milo-overage-output-tokens`, `milo-extra-milo`, `milo-sms-overage`, `milo-priority-support`.
> 2. API endpoints: `POST /v1/billing/checkout` (Checkout session), `POST /v1/billing/portal` (Customer Portal session). Webhook handler for `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`, `customer.subscription.trial_will_end`.
> 3. Trial mechanics per spec Section 11.3: 14 days, **card required at signup**, full caps during trial, auto-charge on expiry.
> 4. Token cap enforcement: middleware checks `usage_meters` before agent runs; at 80% emits a warning notification; at 100% with overage opt-in, continues; at 100% without overage, throttles to Haiku-only and queues Sonnet-grade turns until next period.
> 5. Founding-customer promo: feature-flagged at signup; 50% off Solo or Team for first 6 months on annual plan; expires when promo cap hits 100 tenants. Track via a `promos` table.
> 6. Onboarding wizard: 5-step flow from signup → tenant creation → persona pack pick → Stripe checkout → first integration connect → first program wizard. Each step is a route, the user can resume mid-flow if they drop off.
> 7. Eval scenarios: 5 new scenarios covering trial expiry, overage soft-warn, overage hard-cap with opt-in, downgrade attempt with too many seats, founding-promo redemption.
> 8. Documentation: `docs/runbooks/billing-incident.md` covering Stripe webhook failures and how to manually reconcile.
>
> **Verification gate:**
>
> ```bash
> make lint typecheck test
> uv run pytest -q --cov-fail-under=85
> uv run python tools/eval/runner.py --tag billing
> # Stripe test-mode integration:
> stripe trigger invoice.paid --override invoice:metadata[milo_tenant_id]=$TEST_TENANT_ID
> # Manual full loop: signup → checkout with Stripe test card → verify subscription active → run agent → verify usage metered.
> ```

---

## Phase 10 — Observability, eval suite at 50, deploy hardening

**Goal:** Finalize the PoC for customer-accessible operation: structured logs, metrics, X-Ray traces, full eval suite, deploy pipeline polish, and runbooks.

**Prerequisites:** Phase 9 deployed.

**Prompt to paste into Antigravity:**

> You are implementing Phase 10. Read spec Sections 13 (Observability), 14 (Deployment), and 16 (Success Metrics). Apply §0 standards.
>
> **Deliverables:**
>
> 1. CloudWatch Logs with 7-day retention (PoC mode). Sensitive-field redaction at the logging boundary. Log groups per Lambda; log retention enforced via CDK.
> 2. CloudWatch custom metrics per spec Section 13.2: `tokens_in`, `tokens_out`, `cost_usd`, `tool_calls`, `escalations`, `approvals_pending`. Emitted from the agent runtime after every turn.
> 3. AWS X-Ray on Lambda + Bedrock + RDS calls. Sampling 5% in PoC.
> 4. Sentry SDK in API and web; PostHog SDK in web; Langfuse SDK in agent runtime — all on free tiers in PoC.
> 5. CloudWatch dashboard `milo-poc-overview` with: API p50/p95/p99 latency, error rate, agent run cost / hour, approvals queue depth, tenant signups (24h), token usage (24h).
> 6. CloudWatch alarms: API error rate > 1% over 10m, p95 latency > 5s over 10m, agent cost / hour > $5, queue depth > 50.
> 7. Eval suite expanded to 50 scenarios. CI gate at 95% pass on PR; 100% required for tagged `release-*` deploys.
> 8. GitHub Actions deploy workflow polished: tag-driven, manual approval before `cdk deploy`, posts deploy summary back to the PR.
> 9. Runbooks in `docs/runbooks/`: `incident-response.md`, `customer-deletion.md` (per spec Section 11.6 + 12.4), `bedrock-throttling.md`, `oauth-token-expired.md`, `cost-spike.md`.
> 10. Final spec compliance check: produce `docs/spec-compliance.md` mapping every spec section to the file/module that implements it, marking sections explicitly deferred per Section 6.7 (PoC mode).
> 11. Tag `v0.1.0-poc` and deploy to `milo-poc`.
>
> **Verification gate (the entire PoC must pass this gate before declaring v0.1.0-poc shipped):**
>
> ```bash
> make lint typecheck test
> uv run pytest -q --cov-fail-under=85
> cd apps/web && pnpm test:e2e
> uv run python tools/eval/runner.py --all  # all 50 scenarios; >=95% pass
> cd packages/cdk && pnpm cdk diff -c mode=poc  # no drift
> # Full smoke through the deployed PoC URL:
> tools/scripts/poc_acceptance.sh
> # The acceptance script exercises: signup → checkout → connect Gmail → first program → first message → first approval → approve action → status report → cancel.
> # Cost check:
> aws ce get-cost-and-usage --time-period Start=$(date -d '7 days ago' +%F),End=$(date +%F) --granularity DAILY --metrics UnblendedCost
> # Last-7-day cost must be under $10 (PoC budget).
> ```

---

## Acceptance criteria for the PoC (Phase 10 done = v0.1.0-poc)

The PoC is **acceptance-complete** when, on the deployed `milo-poc` stack, a fresh user can:

1. Visit the marketing site, sign up with email, complete tenant creation, choose persona pack, enter card via Stripe Checkout test mode, and land in the app.
2. Connect a Gmail account via the OAuth flow.
3. Create a program and have Milo conduct a charter intake interview.
4. See Milo draft an email in response to a real message in the connected Gmail inbox.
5. Approve the email and see it land in the Gmail Sent folder.
6. Receive a daily briefing the next morning.
7. Cancel via the Customer Portal and have data preserved for 60 days per spec.

All of the above must complete with cumulative LLM cost under **$0.50** for the full first-session experience and total monthly infrastructure cost (per AWS Cost Explorer) under **$40** for the first 30 days.

---

## Cross-phase guidance for Antigravity

- **Always read the spec doc first.** When a prompt says "per Section N of the spec," open that section before writing code. Antigravity's planner mode produces better breakdowns when grounded in the spec.
- **Prefer planner-then-builder.** Run planner mode first on each phase prompt; have it produce a checklist of file-level tasks; review and trim; then run builder mode against the trimmed list. This catches over-eager scope expansion early.
- **Use the verification gate as a feedback loop.** When a gate fails, paste the failing output back into the same Antigravity session and ask for a remediation plan before applying any fix.
- **Never let Antigravity skip a verification gate.** If it claims a phase is done without running the gate, reject and instruct it to run the gate.
- **Keep the cost ceiling visible.** At the end of every phase, the agent should attach a `aws ce get-cost-and-usage` snapshot to the PR. The PoC budget is $40/month; if a phase pushes monthly forecast above $40, it's a stop-the-line event.
- **Preserve the PoC/Production switch discipline.** Every CDK construct must accept a `mode: 'poc' | 'prod'` flag, even if the prod branch is `throw new Error('not implemented in PoC')` for now. This is what makes the migration path real.

---

## Appendix — Recommended Antigravity setup

Configure these workspace settings before starting Phase 0:

- Pin `Milo_Platform_Build_Specification.docx` v1.3 and this prompts document to the workspace context.
- Enable the multi-agent mode with separate Planner and Builder agents.
- Configure GitHub integration so PRs can be opened directly.
- Set the tool-budget cap at 200 tool calls per phase; this is generous for the largest phases (3, 6, 10) and forces decomposition of smaller phases.
- Set the cost cap at $5 of LLM spend per phase. If a phase exceeds, pause and review.
- Add a custom rule: "Never mark a task complete without running its verification gate and pasting the output into the PR description."
