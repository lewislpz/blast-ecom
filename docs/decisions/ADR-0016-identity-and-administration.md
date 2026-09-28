# ADR-0016: Identity and Administration

## Status

Accepted

## Date

2026-09-28

## Context

A same-origin React client and Django backend need login, ownership checks and administrative tools.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Django database sessions and Django admin | Uses selected framework, server-side revocation and minimal UI work | CSRF and administrative action discipline required |
| JWT access/refresh tokens | Fits independent clients | Refresh/revocation/storage complexity |
| External OIDC provider | Delegates identity operation | External service/cost and integration dependence |

## Decision

Use Django authentication with a custom AbstractUser-based model created in its first migration, unique normalized email login, and database-backed sessions. Use React for customer journeys and Django admin for internal catalog/stock operations. Scope all customer order queries to the authenticated owner. Group/permission-based staff authorization is separate from customer ownership.

Use same-origin /api and /admin access; CSRF protection on all unsafe requests including login and logout. No bearer token storage. Django password hashing and validators, no custom crypto. Staff inventory changes use audited domain actions, not direct stock field editing; order/payment/reservation states are read-only in admin. Anonymous public reads are limited to active catalog data. Registration, login, logout, current identity and password reset are documented in the security baseline. Public deployment has additional gates; a local simulated store is not a secure production claim.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: Admin bypasses, CSRF on anonymous login, object-level data leaks and account abuse require negative tests. Password reset delivery initially uses local development mail only.

## Reversibility

Moderate for client auth migration; changing the user model late is expensive.

## Reconsideration Trigger

Mobile/third-party clients, enterprise identity, public administrative exposure or regulatory requirements.

## Related Decisions and Specifications

- [overview](../security/overview.md).
- [threat-model](../security/threat-model.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
