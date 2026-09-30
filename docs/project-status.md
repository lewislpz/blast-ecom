# Blast Ecom Project Status

Updated: 2026-09-29

## Current Phase

Phase 1 — Core Domain & Application Foundation. Runtime, catalog/inventory, transactional order operations, session/CSRF authentication and owner-scoped order HTTP APIs are implemented and targeted-verified. Next is the customer browser journey.

## Current Objective

Implement task-5 customer browser journey against the verified same-origin session/CSRF and order APIs.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Twenty-one Accepted ADRs total. Original twelve preserved unchanged.
- Backend and frontend dependency locks, checks and starter scaffolds.
- Custom UUID-keyed Django user model with normalized unique email and generated initial migration.
- Fresh PostgreSQL 17.11 connectivity verified through a temporary Docker container; all migrations, including `users.0001_initial`, applied successfully.
- Backend Django system/migration checks, Ruff, mypy, 17 catalog/inventory integration/API/admin tests and OpenAPI validation passed.
- Product/category and stock models, PostgreSQL constraints, transactional audited adjustments, staff-only Django Admin and read-only public catalog API implemented.
- RFC 9457 API exception handling and validated OpenAPI schema implemented; catalog/inventory API/admin/schema tests pass against PostgreSQL.
- Order, item snapshot, stock reservation, payment attempt, idempotency, audit and notification-intent models/migrations and domain operations implemented; PostgreSQL lock/race/replay/rollback tests pass.
- Backend test suite: 50 passed against PostgreSQL 17.11; Ruff, formatting, mypy and migration drift checks pass.
- Session auth API: CSRF bootstrap, local-only registration, generic login, rotating bounded sessions, logout and current-user route.
- Customer order API: owner-scoped list/create/detail/payment-simulation/cancel, strict validation, UUIDv4 idempotency keys and Problem Details.
- OpenAPI regenerated and validates auth/CSRF/idempotency headers and route contracts.
- Frontend `npm ci`, type check, lint, formatting check, one smoke test and production build passed.

Browser implementation, password reset/email verification, shared auth abuse controls, notification delivery, persistent Compose setup and deployment remain unimplemented. API registration is local DEBUG-only; no public-account or production readiness is claimed.

## In Progress

Task task-1 — scaffold and runtime compatibility: complete. Task task-2 — catalog/inventory: complete. Task task-3 — order/reservation/payment/idempotency domain operations: complete. Task task-4 — session/CSRF and owner-scoped API: implementation and targeted verification complete; full-slice high-risk gates remain open.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: generated frontend client, remaining API contract details and empirical query plans.
- Before public accounts: real email verification/reset, shared abuse controls, staff MFA/access restrictions and privacy retention.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: environments/provider/budget, secrets/TLS/networking, backup/restore, RPO/RTO, SLOs and actionable monitoring.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are deliberately deferred; Redis/RabbitMQ or Kubernetes are not required next steps.

## Blockers

The task-1 live database check passed against a disposable container. The reproducible local Compose setup is still pending; public/real-data use remains blocked by launch gates above.

## Known Issues

Git is initialized on `main` and tracks `origin/main`; the scaffold is committed locally. Django/React source and lockfiles exist. Disposable PostgreSQL domain validation passed, but Compose, customer-facing checkout/authentication, browser flow, notification delivery and deployment do not yet exist.

## Technical Debt

No code debt exists. Django coupling, shared storage and local simulation are deliberate choices. Future operational limitations are documented gates, not hidden production readiness.

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
| R-13 | No reproducible local PostgreSQL setup | Add the selected PostgreSQL-only Compose service with safe persistence behavior and document setup | Open |

## Next Steps

1. Implement customer UI over the session and order APIs.
2. Add reproducible PostgreSQL-only Compose setup and restartable maintenance.
3. Add notification/idempotency maintenance and recovery scenarios.
4. Apply full-slice threat-model, integration, independent-review and user-approval gates before declaring the slice complete.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
