# Blast Ecom Project Status

Updated: 2026-09-28

## Current Phase

Phase 1 — Core Domain & Application Foundation. The first implementation increment is in progress; its PostgreSQL migration/connectivity acceptance remains unverified.

## Current Objective

Complete the runtime scaffold against the selected PostgreSQL baseline, then implement catalog and inventory invariants as the next bounded increment.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Twenty-one Accepted ADRs total. Original twelve preserved unchanged.
- Backend and frontend dependency locks, checks and starter scaffolds.
- Custom UUID-keyed Django user model with normalized unique email and generated initial migration.
- Backend Django check, migration drift check (without database-history verification), Ruff, mypy and three pure unit cases passed.
- Frontend `npm ci`, type check, lint, formatting check, one smoke test and production build passed.

The purchase journey, API, authentication flows, catalog, inventory, PostgreSQL runtime and deployment remain unimplemented.

## In Progress

Task task-1 — scaffold and runtime compatibility: code and lockfiles are present. Waiting for an available PostgreSQL 17 service to apply the initial migration and verify the connection before marking the task complete.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: concrete model field lengths, generated schema/client, local configuration and empirical query plans.
- Before public accounts: real email verification/reset, shared abuse controls, staff MFA/access restrictions and privacy retention.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: environments/provider/budget, secrets/TLS/networking, backup/restore, RPO/RTO, SLOs and actionable monitoring.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are deliberately deferred; Redis/RabbitMQ or Kubernetes are not required next steps.

## Blockers

The local implementation environment has no Docker/Compose or PostgreSQL server. Do not begin PostgreSQL-dependent catalog/inventory integration work until task-1's live database check passes. Public/real-data use remains blocked by launch gates above.

## Known Issues

Git is initialized on `main` and tracks `origin/main`; no commit has been made for the implementation in progress. Django/React source and lockfiles now exist. PostgreSQL, Compose, purchase behavior, runtime database tests and deployment do not.

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
| R-12 | Runtime lines mistaken for verified lock set | Exact Python/JS locks and local checks are verified; PostgreSQL runtime check remains pending | Partially resolved |
| R-13 | No local PostgreSQL/Compose available | Add the selected PostgreSQL-only Compose service and verify initial migration/connectivity before domain persistence work | Open |

## Next Steps

1. Provide Docker/Compose or a PostgreSQL 17 server for local development.
2. Apply the custom-user migration and run PostgreSQL-backed scaffold verification.
3. Implement catalog and inventory invariants with PostgreSQL integration tests.
4. Implement orders/reservations, API security and the customer UI in approved-plan order.
5. Apply high-risk threat-model, tests, integration, independent-review and user-approval gates before declaring the slice complete.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
