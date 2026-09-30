# Blast Ecom Project Status

Updated: 2026-09-30

## Current Phase

Phase 1 — Core Domain & Application Foundation. Runtime, catalog/inventory, transactional order operations, session/CSRF authentication, owner-scoped order APIs, customer browser journey and PostgreSQL-only local Compose workflow are implemented. Task-6 integration verification and broader task-7 acceptance remain.

## Current Objective

Run task-7 whole-slice acceptance and documentation reconciliation. Task-4 independent review and explicit approval remain required before the high-risk slice can be declared complete.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Twenty-one Accepted ADRs and one Superseded ADR. The original first eleven records remain unchanged; ADR-0018 preserves its earlier accepted UI state design and is superseded only for type-generation tooling.
- Backend and frontend dependency locks, checks and starter scaffolds.
- Custom UUID-keyed Django user model with normalized unique email and generated initial migration.
- Fresh PostgreSQL 17.11 connectivity verified through a temporary Docker container; all migrations, including `users.0001_initial`, applied successfully.
- Backend Django system/migration checks, Ruff, mypy, 17 catalog/inventory integration/API/admin tests and OpenAPI validation passed.
- Product/category and stock models, PostgreSQL constraints, transactional audited adjustments, staff-only Django Admin and read-only public catalog API implemented.
- RFC 9457 API exception handling and validated OpenAPI schema implemented; catalog/inventory API/admin/schema tests pass against PostgreSQL.
- Order, item snapshot, stock reservation, payment attempt, idempotency, audit and notification-intent models/migrations and domain operations implemented; PostgreSQL lock/race/replay/rollback tests pass.
- Backend test suite: 59 passed against PostgreSQL 17.11; Ruff, formatting, mypy and migration drift checks pass.
- Session auth API: CSRF bootstrap, local-only registration, generic login, rotating bounded sessions, logout and current-user route.
- Customer order API: owner-scoped list/create/detail/payment-simulation/cancel, strict validation, UUIDv4 idempotency keys and Problem Details.
- OpenAPI regenerated and validates auth/CSRF/idempotency headers and route contracts.
- React storefront routes for catalog, product detail, in-memory cart, local account, checkout and own order history/payment simulation/cancellation.
- Same-origin CSRF/session API adapter with generated OpenAPI types, explicit API errors, non-retrying idempotent mutations and server-owned prices/outcomes.
- Frontend catalog/cart and API adapter tests plus Playwright registration, checkout, simulated payment, cancellation and order-history E2E against the local stack.
- Frontend dependency install, clean npm audit, type check, lint, formatting, unit/component tests and production build pass. Playwright browser purchase and Axe accessibility checks pass against the local stack.
- PostgreSQL-only Compose service uses a loopback-bound port, explicit health check and persistent named volume; fresh migrations, safe fictional seed, and bounded maintenance commands are implemented.
- Database readiness performs a live query; API database connectivity failures return a generic 503. Seed and maintenance commands require local DEBUG configuration; seeding additionally requires an explicit environment opt-in.

Password reset/email verification, shared auth abuse controls, notification delivery, backups and deployment remain unimplemented. API registration is local DEBUG-only; no public-account or production readiness is claimed.

## In Progress

Task task-1 — scaffold and runtime compatibility: complete. Task task-2 — catalog/inventory: complete. Task task-3 — order/reservation/payment/idempotency domain operations: complete. Task task-4 — session/CSRF and owner-scoped API: implemented and verified; independent review and explicit approval gates remain open. Task task-5 — browser journey: implemented, verified, checkpointed and committed. Task task-6 — local PostgreSQL and maintenance: implemented, verified and checkpointed; commit pending.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: remaining API contract details and empirical query plans.
- Before public accounts: real email verification/reset, shared abuse controls, staff MFA/access restrictions and privacy retention.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: environments/provider/budget, secrets/TLS/networking, backup/restore, RPO/RTO, SLOs and actionable monitoring.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are deliberately deferred; Redis/RabbitMQ or Kubernetes are not required next steps.

## Blockers

Task-4 independent security review and explicit user approval are still required for high-risk slice completion. Public/real-data use remains blocked by launch gates above.

## Known Issues

Git is initialized on `main` and tracks `origin/main`; the core API and verified browser slices are committed locally. The current PostgreSQL/maintenance increment is uncommitted. Notification delivery and deployment remain unimplemented.

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
| R-07 | Admin bypasses | Restricted actions and negative tests | Open |
| R-08 | Shared DB failure/resource scope | Recovery/capacity design before hosted use | Open |
| R-09 | Migration locks/data loss | Review and clean/upgrade/recovery validation | Open |
| R-10 | Local auth defaults mistaken for public readiness | Threat model and public-account gates | Open |
| R-11 | Maintenance delay holds stock | Deadline checks, durable state, backlog visibility | Open |
| R-12 | Runtime lines mistaken for verified lock set | Exact Python/JS locks and local checks are verified; PostgreSQL 17.11 connection and initial migration are now verified | Resolved for scaffold |
| R-13 | No reproducible local PostgreSQL setup | PostgreSQL-only Compose service with persistent named volume, loopback binding and documented setup | Resolved for local development |

## Next Steps

1. Commit the verified task-6 implementation locally and bind the resulting state.
2. Continue task-7 end-to-end acceptance and reconcile documentation.
3. Obtain task-4 independent review and explicit user approval; retain these as blockers until recorded.
4. Apply full-slice threat-model, integration and review gates before declaring the slice complete.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
