# Blast Ecom Project Status

Updated: 2026-10-04

## Current Phase

Phase 3 — Testing & pre-production hardening. The local commerce slice and Compose platform are implemented and committed. Public-account foundations and Stripe sandbox integration code are implemented; live SMTP/payment, hosted recovery, CI and real deployment are not yet verified or complete. No hosted production environment is claimed.

## Current Objective

The local-development milestone is complete and verified. Production image targets and the least-privilege CI workflow are implemented; local image builds and smoke tests pass. The API image has 44 HIGH findings across eight Debian-tracked CVEs; an exact 30-day exception set exists for those OS-package tuples only, with all other findings still blocking. Unit, threat-model and local scan integration checks pass; the independent reviewer’s fail-closed findings have been fixed and await final confirmation. Hosted GitHub execution is still required before treating main-branch artifacts as reviewed. Live email delivery, payment settlement, hosted backup policy/lifecycle and public deployment still require provider accounts, credentials, infrastructure and operational validation not present in this workspace; code can be prepared and sandbox-tested without claiming those external outcomes.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Thirty-one Accepted ADRs and two Superseded ADRs. The original first eleven records remain unchanged; ADR-0018 preserves its earlier accepted UI state design and is superseded only for type-generation tooling.
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
- Opt-in S3-compatible PostgreSQL backup/restore requires a versioned bucket, requests and verifies SSE-S3, exact object versions, metadata/tags, object bytes and SHA-256 before success; restore targets only a new database distinct from the source. Moto S3 API plus disposable PostgreSQL 17.11 round-trip verification preserved representative product/order/user counts. This does not configure hosted bucket policy, lifecycle enforcement, credentials, scheduling, alerts or recovery objectives.
- Production API and frontend container targets exist: Gunicorn/WhiteNoise for Django and unprivileged Nginx for static SPA. Python and Nginx image builds apply current signed OS-package updates; the API runtime omits pip/ensurepip. Local builds and runtime smoke tests pass. Trivy 0.74.0 reports no HIGH/CRITICAL findings in the frontend image and 44 API OS-package tuples across eight Debian CVEs. ADR-0033 adds exact, expiring exceptions only for those current tuples; independent review and local policy integration remain in progress. The findings remain present in the image. The read-only GitHub Actions workflow has not run in GitHub or been made a required branch check.

The reviewed Group-admin privilege-escalation path is closed in the current implementation: ordinary staff cannot access Group administration, while active staff superusers retain break-glass access. External notification delivery remains unimplemented; local console messages are simulations. Remote backup/restore application code exists, but hosted operation and production recovery remain unverified. Current auth attempt limits are application-level only. API registration, password reset, demo verification, notification processing and local backup commands are DEBUG-only; no real mailbox ownership, public-account or production readiness is claimed. Remote dump staging uses plaintext in private temporary storage, which remains a hosted deployment risk to mitigate.

## In Progress

Production-readiness hardening is in progress. The local account experience remains unchanged; fail-closed production settings, explicit trusted-proxy parsing, cross-source identity limits, verified-account enforcement and a bounded SMTP outbox are implemented. Stripe-hosted sandbox checkout, signature-verified minimal webhook receipts, manual capture and safe retry/late-event handling are implemented. The opt-in S3-compatible backup workflow and local PostgreSQL restore drill are implemented. Full verification details are recorded in the active hardening plan and its gate evidence. SMTP has only been exercised through a test backend; real Stripe sandbox delivery has not been validated because credentials/account are unavailable. Hosted backup policy/lifecycle/credentials and CI/deployment/operations remain incomplete. The application is not ready for public or real-customer use.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: remaining API contract details and empirical query plans.
- Before public accounts: externally validate production settings and proxy topology; verify SMTP/sender-domain delivery; supervise and alert on outbox work; establish shared/edge volumetric controls, staff MFA/access restrictions, privacy retention/erasure and a production security review. Application-level verified-email gating is implemented but does not satisfy these operational gates.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: provider/account/credentials, secrets/TLS/networking, least-privilege bucket policy, lifecycle enforcement, protected temporary storage, scheduled encrypted/versioned backups, hosted restore drill, agreed RPO/RTO, SLOs and actionable monitoring. Provider-independent code and disposable-service tests can be built before an account is available.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are active readiness work items, not claims that the capability exists. Redis/RabbitMQ or Kubernetes are not mandatory next steps; adoption must still be justified by deployment needs.

## Blockers

No blocker for local development. Real public operation still requires provider credentials, hosted infrastructure, external security/operational validation and commercial requirements. These do not prevent provider-independent application work or sandbox tests.

## Known Issues

External notification delivery, hosted backup operations, CI and production deployment remain incomplete. The current Stripe sandbox implementation is pending a real provider-account/webhook exercise. Production-hardening work is committed locally as increments; no push or hosted deployment is performed.

## Technical Debt

Known debt: `frontend/src/styles/global.css` currently centralizes all UI styles rather than scoping them as CSS Modules. Split/scope styles when component ownership settles; do not add a styling framework solely to address this. Django coupling, shared storage and local simulation are deliberate choices. Future operational limitations are documented gates, not hidden production readiness.

## Risks

| ID   | Risk                                                           | Mitigation                                                                                                                                                                        | Status                                                                           |
| ---- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| R-01 | Commerce model ambiguity                                       | Single seller/physical goods/EUR accepted                                                                                                                                         | Resolved                                                                         |
| R-02 | Scope expansion                                                | Bounded first slice and explicit exclusions                                                                                                                                       | Open                                                                             |
| R-03 | Cross-module coupling                                          | Owner operations, selectors, explicit FKs and future tests                                                                                                                        | Open                                                                             |
| R-04 | Unknown capacity/budget/team                                   | No invented SLOs or sizing; gather before hosting                                                                                                                                 | Open                                                                             |
| R-05 | SPA catalog search limitations                                 | Public SEO requirement gate                                                                                                                                                       | Open                                                                             |
| R-06 | Real tax/shipping unspecified                                  | Demo-only labels/defaults; real-sales gate                                                                                                                                        | Open                                                                             |
| R-07 | Staff self-escalation through Django Group admin               | Group admin restricted to active staff superusers; negative tests cover list/add/change/delete access and mutation routes                                                         | Resolved for local development; superuser credential protection remains required |
| R-08 | Shared DB failure/resource scope                               | Recovery/capacity design before hosted use                                                                                                                                        | Open                                                                             |
| R-09 | Migration locks/data loss                                      | Review and clean/upgrade/recovery validation                                                                                                                                      | Open                                                                             |
| R-10 | Local auth defaults mistaken for public readiness              | Threat model and public-account gates                                                                                                                                             | Open                                                                             |
| R-11 | Maintenance delay holds stock                                  | Deadline checks, durable state, backlog visibility                                                                                                                                | Open                                                                             |
| R-12 | Runtime lines mistaken for verified lock set                   | Exact Python/JS locks and local checks are verified; PostgreSQL 17.11 connection and initial migration are now verified                                                           | Resolved for scaffold                                                            |
| R-13 | No reproducible local PostgreSQL setup                         | Compose API, frontend, PostgreSQL and maintenance with named persistence, health checks and documented migration/seed workflow                                                    | Resolved for local development                                                   |
| R-14 | Remote backup policy and temporary plaintext exposure          | Require exact version/read-back checksum; restrict temp permissions; configure least-privilege hosted identity, protected ephemeral storage and tested lifecycle before real data | Open — hosted environment not provisioned                                        |
| R-15 | CI/production image workflow not validated on GitHub           | Run the workflow and configure required checks/reviews after repository integration; audit action pins and scanner output                                                         | Open — hosted workflow run unavailable                                           |
| R-16 | Temporarily accepted Debian API image findings or policy drift | Exact CVE/package/version/distro matches, 30-day expiry, fail-closed stale-entry checks, visible output, independent review; require capability restrictions before hosted use    | Open — 44 findings remain in image; expires 2026-11-03                           |

## Next Steps

1. Run CI in the connected GitHub repository, review scans and configure required branch checks.
2. Provision and independently validate hosted backup permissions, lifecycle, scheduling, monitoring and recovery after an environment is selected.
3. When secure provider credentials/accounts become available, verify real Stripe sandbox delivery and SMTP; verify recovery and production readiness in a real hosted environment before public launch.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
