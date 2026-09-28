# Blast Ecom Project Status

Updated: 2026-09-28

## Current Phase

Phase 0 — Product Definition & Architecture. Initial local implementation baseline is documented; no application implementation has started.

## Current Objective

Hand off a cohesive local simulated purchase specification and prepare bounded implementation work when requested.

## Completed

- ADR-0001 through ADR-0012: user-selected product, architecture, stack, storage ownership and persistence foundations.
- ADR-0013 through ADR-0021: nine grouped decisions selected by Codex under explicit user delegation on 2026-09-28.
- Product lifecycle, data model/locks, account/admin policy, API/idempotency, frontend, tooling, local runtime, testing, migrations and observability specifications.
- Initial threat model, acceptance matrix, decision register and decision report.
- Twenty-one Accepted ADRs total. Original twelve preserved unchanged.

These are design/documentation outcomes. No application capability is Implemented.

## In Progress

Decision round complete: documentation consistency checks passed and the first-slice baseline is ready for handoff. Application implementation has not been requested in this round.

## Pending Decisions

See the [decision register](roadmap/decision-register.md) for complete trigger-based deferrals.

- Implementation details: exact locked patches/tool versions, concrete model field lengths, generated schema/client, local configuration and empirical query plans.
- Before public accounts: real email verification/reset, shared abuse controls, staff MFA/access restrictions and privacy retention.
- Before real sales: markets/jurisdiction, taxes/invoicing, actual shipping charges/coverage and fulfillment.
- Before hosted operations: environments/provider/budget, secrets/TLS/networking, backup/restore, RPO/RTO, SLOs and actionable monitoring.
- Conditional: broker/cache, external payments/events, tracing, Kubernetes/Helm/GitOps/Terraform and scaling.

These are deliberately deferred; Redis/RabbitMQ or Kubernetes are not required next steps.

## Blockers

No unresolved architecture choice blocks preparing the local simulated first-slice implementation plan. Exact dependency compatibility and behavioral correctness must be verified during implementation. Public/real-data use remains blocked by launch gates above.

## Known Issues

No Git repository, application, lockfiles, runnable app tests, database or deployment exists. Historical ADRs describe pending topics at their creation; active specs and later ADRs refine them.

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
| R-12 | Runtime lines mistaken for verified lock set | Resolve exact versions and run compatibility checks | Open |

## Next Steps

1. Prepare a small implementation plan based on [first slice](development/first-slice.md) when requested.
2. Verify runtime/dependency locks and custom-user migration ordering.
3. Implement domain invariants with real PostgreSQL tests.
4. Apply high-risk implementation gates to authentication/authorization.
5. Update docs against actual behavior as increments are completed.

## Latest Report

[Phase 0 delegated decisions report](reports/2026-09-28-phase0-decisions.md).
