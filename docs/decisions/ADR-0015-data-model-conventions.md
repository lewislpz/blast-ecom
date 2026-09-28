# ADR-0015: Data Model and Transaction Conventions

## Status

Accepted

## Date

2026-09-28

## Context

Identifiers, money, relations and lock rules must support the selected lifecycle.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| UUIDv4 and exact decimals with Django constraints | Native UUID type, simple generation, explicit money precision | Larger indexes than integer IDs |
| Sequential IDs | Compact indexes and simple ordering | Predictable public IDs and tighter central generation |
| UUIDv7/ULID | Time-oriented identifiers | Extra generation/version conventions; time information exposed |

## Decision

Use UUIDv4 primary keys for domain entities and native PostgreSQL UUID storage. Technical Django tables may retain framework IDs. Persist amounts as DecimalField(max_digits=12, decimal_places=2), EUR only; API money is a two-decimal string. Use timezone-aware UTC timestamps. Preserve SKU, title, unit price, currency and address snapshots on orders.

Allow explicitly listed cross-module foreign keys within the shared database, with PROTECT for historical references. Ownership still controls writes. Use thin API serializers, module services for commands, selectors for cross-module reads and ORM models for persistence. Use READ COMMITTED with explicit atomic blocks and row locks for inventory/order transitions. The model specification defines lock order, unique constraints and acceptance tests. No generic repository framework, event sourcing, blanket soft-delete or unrestricted cross-module QuerySets.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: UUIDs do not authorize access. Decimal bounds need validation on aggregates. Shared foreign keys make later extraction work explicit.

## Reversibility

Moderate to expensive for identifier/amount changes after public contracts exist.

## Reconsideration Trigger

Measured indexing issues, new currencies, ownership extraction or different stock granularity.

## Related Decisions and Specifications

- [data-architecture](../architecture/data-architecture.md).
- [application-structure](../architecture/application-structure.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
