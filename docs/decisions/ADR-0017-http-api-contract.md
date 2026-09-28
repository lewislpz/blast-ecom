# ADR-0017: HTTP Contract and Idempotency

## Status

Accepted

## Date

2026-09-28

## Context

The frontend needs explicit contracts and mutation retries must not duplicate stock/payment effects.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Versioned JSON REST and generated OpenAPI | Fits DRF and typed clients | Schema and behavior need contract tests |
| Unversioned ad-hoc JSON | Less initial policy | Harder evolution and inconsistent failures |
| GraphQL | Flexible query selection | Additional contract/authorization layer not justified |

## Decision

Use /api/v1/ JSON resources, snake_case fields, explicit POST command endpoints for payment and cancellation, drf-spectacular for OpenAPI 3, and RFC 9457 Problem Details with stable code, request_id and field_errors extensions. Use page-number lists (20 default, 100 maximum), deterministic ordering and allowlisted filters.

Require Idempotency-Key for order creation, payment and cancellation. Persist a scoped key/fingerprint/result in PostgreSQL atomically with business changes, serialize concurrent equal keys, reject changed payload with 409 and retain results for at least 24 hours. Replay stored status/body after rechecking access; fetch current state via GET. Never trust client user IDs, prices, totals or states as authority. No automatic retries of mutations with a fresh key.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: Schema generation alone does not prove access control or idempotency. Reusing a key after retention can start a new operation; clients must use unique keys.

## Reversibility

Moderate to expensive once external clients depend on contracts.

## Reconsideration Trigger

New client capabilities, measured pagination costs or incompatible API changes.

## Related Decisions and Specifications

- [standards](../api/standards.md).
- [idempotency](../api/idempotency.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
