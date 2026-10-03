# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-0001](ADR-0001-v1-scope.md) | V1 Scope | Accepted | 2026-09-28 |
| [ADR-0002](ADR-0002-application-architecture.md) | Application Architecture | Accepted | 2026-09-28 |
| [ADR-0003](ADR-0003-repository-strategy.md) | Repository Strategy | Accepted | 2026-09-28 |
| [ADR-0004](ADR-0004-initial-domain-boundaries.md) | Initial Domain Boundaries | Accepted | 2026-09-28 |
| [ADR-0005](ADR-0005-commerce-model.md) | Initial Commerce Model | Accepted | 2026-09-28 |
| [ADR-0006](ADR-0006-backend-stack.md) | Backend Stack | Accepted | 2026-09-28 |
| [ADR-0007](ADR-0007-frontend-stack.md) | Frontend Stack | Accepted | 2026-09-28 |
| [ADR-0008](ADR-0008-database-engine.md) | Database Engine | Accepted | 2026-09-28 |
| [ADR-0009](ADR-0009-api-framework.md) | API Framework | Accepted | 2026-09-28 |
| [ADR-0010](ADR-0010-data-organization.md) | Data Organization | Accepted | 2026-09-28 |
| [ADR-0011](ADR-0011-module-data-ownership.md) | Module Data Ownership | Accepted | 2026-09-28 |
| [ADR-0012](ADR-0012-persistence-tooling.md) | Persistence Tooling | Accepted | 2026-09-28 |
| [ADR-0013](ADR-0013-initial-product-behavior.md) | Initial Product Behavior | Accepted | 2026-09-28 |
| [ADR-0014](ADR-0014-order-reservation-lifecycle.md) | Order and Reservation Lifecycle | Accepted | 2026-09-28 |
| [ADR-0015](ADR-0015-data-model-conventions.md) | Data Model and Transaction Conventions | Accepted | 2026-09-28 |
| [ADR-0016](ADR-0016-identity-and-administration.md) | Identity and Administration | Accepted | 2026-09-28 |
| [ADR-0017](ADR-0017-http-api-contract.md) | HTTP Contract and Idempotency | Accepted | 2026-09-28 |
| [ADR-0018](ADR-0018-frontend-conventions.md) | Frontend State and UI Conventions | Accepted | 2026-09-28 |
| [ADR-0019](ADR-0019-tooling-and-local-development.md) | Tooling and Local Development | Accepted | 2026-09-28 |
| [ADR-0020](ADR-0020-quality-and-migration-policy.md) | Quality, Git and Migration Policy | Accepted | 2026-09-28 |
| [ADR-0021](ADR-0021-operations-baseline-and-deferrals.md) | Operational Baseline and Deferred Infrastructure | Accepted | 2026-09-28 |
| [ADR-0022](ADR-0022-api-type-generator.md) | Frontend OpenAPI Type Generator | Accepted | 2026-09-30 |
| [ADR-0023](ADR-0023-break-glass-group-administration.md) | Break-Glass Group Administration | Accepted | 2026-09-30 |
| [ADR-0024](ADR-0024-authentication-attempt-limits.md) | Authentication Attempt Limits | Accepted | 2026-10-01 |
| [ADR-0025](ADR-0025-local-account-recovery-and-email-verification.md) | Local Account Recovery and Email Verification | Accepted | 2026-10-01 |
| [ADR-0026](ADR-0026-local-notification-processing.md) | Restart-Safe Local Notification Processing | Accepted | 2026-10-01 |
| [ADR-0027](ADR-0027-local-postgresql-backup-and-restore.md) | Safe Local PostgreSQL Backup and Restore | Accepted | 2026-10-01 |
| [ADR-0028](ADR-0028-local-application-container-workflow.md) | Local Application Container Workflow | Accepted | 2026-10-01 |
| [ADR-0029](ADR-0029-public-account-security-and-email-delivery.md) | Public Account Security and Email Delivery Boundary | Accepted | 2026-10-01 |
| [ADR-0030](ADR-0030-stripe-sandbox-checkout.md) | Stripe Sandbox Checkout and Manual Capture | Accepted | 2026-10-01 |
| [ADR-0031](ADR-0031-versioned-remote-database-backups.md) | Versioned Remote Database Backups | Accepted | 2026-10-03 |
| [ADR-0032](ADR-0032-ci-security-and-artifact-boundary.md) | CI Security and Artifact Boundary | Accepted | 2026-10-03 |

## Policy

Significant architectural decisions require explicit user selection or explicit delegated decision authority before becoming Accepted. ADR-0013 through ADR-0021 were selected by Codex under the user's 2026-09-28 delegation; the earlier records were selected individually by the user. Delegation for this round does not silently authorize future unrelated decisions. Records include alternatives, consequences, reversibility, triggers and provenance.

Allowed ADR states: Proposed, Accepted, Rejected, Superseded, Deprecated. Deferred topics stay in [project status](../project-status.md) until a meaningful proposal exists.

Update this table in the same change as any ADR creation or status change. A consistency check compares it with ADR contents during documentation verification. Local CI workflow configuration is implemented under ADR-0032; no hosted run or required-check enforcement has been verified yet.

If a decision changes, preserve its history: mark the old ADR Superseded, create a new Accepted ADR after user selection and link both records.

Discussion Decisions 001–004 map to ADR-0001–ADR-0004 in this initial round. Product scope is recorded because it constrains the architecture.
