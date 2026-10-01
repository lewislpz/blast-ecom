# Blast Ecom Project Status

Updated: 2026-10-01

## Current Phase

Phase 1 — Core Domain & Application Foundation. Runtime, catalog/inventory, transactional order operations, session/CSRF authentication, owner-scoped order APIs, customer browser journey, PostgreSQL-only local Compose workflow and application-level authentication attempt limits are implemented, independently reviewed and locally committed. Hosted/public readiness is explicitly out of scope.

## Current Objective

Continue local-development account recovery/email and notification workflows, followed by verified local backup/restore and a reproducible application deployment path. Keep third-party email delivery and hosted/public production outside scope until the required external inputs and controls exist.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Twenty-three Accepted ADRs and one Superseded ADR. The original first eleven records remain unchanged; ADR-0018 preserves its earlier accepted UI state design and is superseded only for type-generation tooling.
- Backend and frontend dependency locks, checks and starter scaffolds.
- Custom UUID-keyed Django user model with normalized unique email and generated initial migration.
- Fresh PostgreSQL 17.11 connectivity verified through a temporary Docker container; all migrations, including `users.0001_initial`, applied successfully.
- Backend Django system/migration checks, Ruff, mypy, 17 catalog/inventory integration/API/admin tests and OpenAPI validation passed.
- Product/category and stock models, PostgreSQL constraints, transactional audited adjustments, staff-only Django Admin and read-only public catalog API implemented.
- RFC 9457 API exception handling and validated OpenAPI schema implemented; catalog/inventory API/admin/schema tests pass against PostgreSQL.
- Order, item snapshot, stock reservation, payment attempt, idempotency, audit and notification-intent models/migrations and domain operations implemented; PostgreSQL lock/race/replay/rollback tests pass.
- Backend test suite: 73 passed against PostgreSQL 17.11, including Group-admin permission-boundary regressions; Ruff, formatting, mypy, Django system check and migration drift checks pass.
- Session auth API: CSRF bootstrap, local-only registration, generic login, rotating bounded sessions, logout and current-user route.
- Customer order API: owner-scoped list/create/detail/payment-simulation/cancel, strict validation, UUIDv4 idempotency keys and Problem Details.
- OpenAPI regenerated and validates auth/CSRF/idempotency headers and route contracts.
- React storefront routes for catalog, product detail, in-memory cart, local account, checkout and own order history/payment simulation/cancellation.
- Same-origin CSRF/session API adapter with generated OpenAPI types, explicit API errors, non-retrying idempotent mutations and server-owned prices/outcomes.
- Frontend catalog/cart and API adapter tests plus Playwright registration, checkout, simulated payment, cancellation and order-history E2E against the local stack.
- Frontend dependency install, clean npm audit, type check, lint, formatting, unit/component tests and production build pass. Playwright browser purchase and Axe accessibility checks pass against the local stack.
- Task-7 local acceptance rerun: backend 73 PostgreSQL tests, Django system/migration checks, Ruff, formatting and mypy passed; frontend 5 unit/component tests, typecheck, lint, formatting, build and production dependency audit passed; OpenAPI TypeScript regeneration produced no diff; full Chromium purchase and accessibility E2E passed against a fresh PostgreSQL database on a temporary in-memory filesystem. CSRF tests reject untrusted Origin across unsafe customer auth/order API routes.
- PostgreSQL-only Compose service uses a loopback-bound port, explicit health check and persistent named volume; fresh migrations, safe fictional seed, and bounded maintenance commands are implemented.
- Database readiness performs a live query; API database connectivity failures return a generic 503. Seed and maintenance commands require local DEBUG configuration; seeding additionally requires an explicit environment opt-in.
- PostgreSQL-backed HMAC-pseudonymous authentication attempt limits cover customer login, DEBUG-only registration and Django Admin login. Fixed-window counters are atomic, bounded at `limit + 1`, cleaned up by bounded local maintenance and tested for concurrency, CSRF ordering, privacy and failure behavior.
- Authentication abuse-control increment was independently reviewed with no blocking findings; the complete backend suite passes (90 PostgreSQL tests), focused auth/maintenance integration passes (19 tests), frontend checks pass and commit `d4d2419` records the implementation.

The reviewed Group-admin privilege-escalation path is closed in the current implementation: ordinary staff cannot access Group administration, while active staff superusers retain break-glass access. Password reset/email verification and external notification delivery remain unimplemented; current auth attempt limits are application-level only. Backups and hosted deployment remain unimplemented. API registration is local DEBUG-only; no public-account or production readiness is claimed.

## In Progress

Task task-1 — scaffold and runtime compatibility: complete. Task task-2 — catalog/inventory: complete. Task task-3 — order/reservation/payment/idempotency domain operations: complete. Task task-4 — session/CSRF and owner-scoped API: implemented, reviewed, remediated and verified. Task task-5 — browser journey: implemented, verified, checkpointed and committed locally. Task task-6 — local PostgreSQL and maintenance: implemented, verified, checkpointed and committed locally. Task task-7 — whole-slice acceptance: complete for the previously accepted local scope. Auth abuse-control increment: independently reviewed, fully verified and committed locally as `d4d2419`.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: remaining API contract details and empirical query plans.
- Before public accounts: verified real email delivery for account recovery/ownership, trusted proxy parsing, edge/shared abuse controls and monitoring, staff MFA/access restrictions and privacy retention. Development email workflows do not satisfy these production gates.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: environments/provider/budget, secrets/TLS/networking, backup/restore, RPO/RTO, SLOs and actionable monitoring.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are deliberately deferred; Redis/RabbitMQ or Kubernetes are not required next steps.

## Blockers

No known blocker for the documented local-development scope. Shared/public deployment and real-customer data remain blocked by the launch gates above.

## Known Issues

Git is initialized on `main` and tracks `origin/main`; the core API, browser and local PostgreSQL/maintenance increments are committed locally and have not been pushed. External notification delivery, backup/restore automation and hosted deployment remain unimplemented.

## Technical Debt

Known debt: `frontend/src/styles/global.css` currently centralizes all UI styles rather than scoping them as CSS Modules. Split/scope styles when component ownership settles; do not add a styling framework solely to address this. Django coupling, shared storage and local simulation are deliberate choices. Future operational limitations are documented gates, not hidden production readiness.

## Risks

| ID | Risk | Mitigation | Status |
|---|---|---|---|
| R-01 | Commerce model ambiguity | Single seller/physical goods/EUR accepted | Resolved |
| R-02 | Scope expansion | Bounded first slice and explicit exclusions | Open |
| R-03 | Cross-module coupling | Owner operations, selectors, explicit FKs and future tests | Open |
| R-04 | Unknown capacity/budget/team | No invented SLOs or sizing; gather before hosting | Open |
| R-05 | SPA catalog search limitations | Public SEO requirement gate | Open |
| R-06 | Real tax/shipping unspecified | Demo-only labels/defaults; real-sales gate | Open |
| R-07 | Staff self-escalation through Django Group admin | Group admin restricted to active staff superusers; negative tests cover list/add/change/delete access and mutation routes | Resolved for local development; superuser credential protection remains required |
| R-08 | Shared DB failure/resource scope | Recovery/capacity design before hosted use | Open |
| R-09 | Migration locks/data loss | Review and clean/upgrade/recovery validation | Open |
| R-10 | Local auth defaults mistaken for public readiness | Threat model and public-account gates | Open |
| R-11 | Maintenance delay holds stock | Deadline checks, durable state, backlog visibility | Open |
| R-12 | Runtime lines mistaken for verified lock set | Exact Python/JS locks and local checks are verified; PostgreSQL 17.11 connection and initial migration are now verified | Resolved for scaffold |
| R-13 | No reproducible local PostgreSQL setup | PostgreSQL-only Compose service with persistent named volume, loopback binding and documented setup | Resolved for local development |

## Next Steps

1. Implement and test local account recovery/email flows using Django's development console email backend; do not claim mailbox ownership verification from console output alone.
2. Complete local notification processing and verify that a failed/restarted worker preserves intent safely.
3. Add explicit local PostgreSQL backup/restore commands and test restoring into a separate disposable database.
4. Make the application reproducibly runnable as local containers before evaluating hosted deployment.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
