# Blast Ecom Project Status

Updated: 2026-10-02

## Current Phase

Phase 3 — Testing & pre-production hardening. The local commerce slice and Compose platform are implemented and committed. Public-account foundations and Stripe sandbox integration code are implemented; live SMTP/payment, hosted recovery, CI and real deployment are not yet verified or complete. No hosted production environment is claimed.

## Current Objective

The local-development milestone is complete and verified. The current objective is to harden public account flows and progressively build/test the remaining external integration and operational layers. Live email delivery, payment settlement, hosted backups and public deployment require provider accounts, credentials, infrastructure and operational validation not present in this workspace; code can be prepared and sandbox-tested without claiming those external outcomes.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Twenty-nine Accepted ADRs and one Superseded ADR. The original first eleven records remain unchanged; ADR-0018 preserves its earlier accepted UI state design and is superseded only for type-generation tooling.
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
- DEBUG-only local password recovery and demo email verification implemented with Django console email, one-hour tokens, generic recovery responses, PostgreSQL-backed attempt limits, CSRF, password validation, session invalidation and one-use verification marking. Existing demo accounts remain usable without being falsely marked verified. Backend/frontend checks and Chromium recovery E2E pass; independent review found no remaining scoped security findings.
- DEBUG-only local notification processing uses bounded PostgreSQL `skip_locked` claims, records retry metadata, prioritizes never-attempted intents and leaves failed work pending. PostgreSQL tests cover retry after failure/restart, concurrent worker claims and DEBUG-only execution. Messages are printed only through Django's console email backend; external delivery is not implemented.
- DEBUG-only local PostgreSQL backup/restore commands now use custom-format archives, owner-only backup file permissions, no-overwrite backup paths outside the application build context and fresh-database-only restore. Command safety tests pass, and an actual custom-format dump/restore round trip against a disposable PostgreSQL 17.11 database preserved catalog, stock and user counts. This does not constitute production backup/DR.
- Containerized local development includes locked Python/Node dependencies, non-root API/frontend images, loopback-only browser/database ports, persistent PostgreSQL storage, internal service networking and explicit migration/seed operations. Fresh migrations, all service health checks, frontend-to-API catalog access and the Chromium purchase/account/accessibility E2E journey passed. Docker Compose is not a production deployment.

The reviewed Group-admin privilege-escalation path is closed in the current implementation: ordinary staff cannot access Group administration, while active staff superusers retain break-glass access. External notification delivery remains unimplemented; local console messages are simulations. Hosted backup/restore and production application images remain unimplemented. Current auth attempt limits are application-level only. API registration, password reset, demo verification, notification processing and local backup commands are DEBUG-only; no real mailbox ownership, public-account or production readiness is claimed.

## In Progress

Production-readiness hardening is in progress. The local account experience remains unchanged; fail-closed production settings, explicit trusted-proxy parsing, cross-source identity limits, verified-account enforcement and a bounded SMTP outbox are implemented. Stripe-hosted sandbox checkout, signature-verified minimal webhook receipts, manual capture and safe retry/late-event handling are implemented. The 164-test PostgreSQL backend suite, backend static/config/schema checks, frontend checks/build and four Chromium E2E tests pass. Independent payment review found no blocking code findings. SMTP has only been exercised through a test backend; real Stripe sandbox delivery has not been validated because credentials/account are unavailable. Hosted backup/DR, CI and deployment/operations remain later increments. The application is not ready for public or real-customer use.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: remaining API contract details and empirical query plans.
- Before public accounts: externally validate production settings and proxy topology; verify SMTP/sender-domain delivery; supervise and alert on outbox work; establish shared/edge volumetric controls, staff MFA/access restrictions, privacy retention/erasure and a production security review. Application-level verified-email gating is implemented but does not satisfy these operational gates.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: provider/account/credentials, secrets/TLS/networking, encrypted/versioned backup and restore drill, agreed RPO/RTO, SLOs and actionable monitoring. Provider-independent code and disposable-service tests can be built before an account is available.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are active readiness work items, not claims that the capability exists. Redis/RabbitMQ or Kubernetes are not mandatory next steps; adoption must still be justified by deployment needs.

## Blockers

No blocker for local development. Real public operation still requires provider credentials, hosted infrastructure, external security/operational validation and commercial requirements. These do not prevent provider-independent application work or sandbox tests.

## Known Issues

External notification delivery, hosted backup/restore, CI and production deployment remain unimplemented. The current Stripe sandbox implementation is pending a real provider-account/webhook exercise. Production-hardening work is committed locally as increments; no push or hosted deployment is performed.

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
| R-13 | No reproducible local PostgreSQL setup | Compose API, frontend, PostgreSQL and maintenance with named persistence, health checks and documented migration/seed workflow | Resolved for local development |

## Next Steps

1. Implement hosted encrypted backup and automated restore-drill workflow.
2. Add CI and production artifact gates, then deployment/operations controls.
3. When secure provider credentials/accounts become available, verify real Stripe sandbox delivery and SMTP; verify recovery and production readiness in a real hosted environment before public launch.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
