# ADR-0011: Module Data Ownership

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is a planned Django/DRF modular monolith with six logical domains and PostgreSQL. No database or application is implemented.

## Decision Drivers

- Keep initial development and operation proportionate.
- Maintain clear module responsibilities.
- Support reliable order and inventory operations without premature distribution.

## Options Considered

| Option | Benefits | Costs and risks |
|---|---|---|
| Module-controlled writes | Centralized business rules and clearer evolution boundaries | Internal operations and enforcement need design |
| Direct cross-module writes | Less initial interface work | Rules become scattered and ownership/extraction become harder |

## Decision

Each persisted business table has one owning module. Other modules request changes through explicit in-process operations of that owner; they do not directly modify its tables.

## Approval

The project owner answered "lo recomendado" on 2026-09-28 after recommendations A for both data topology and write ownership. This record documents that explicit choice.

## Consequences

Orders can ask Inventory to reserve stock, while Inventory validates and changes its own data. This is an example, not an accepted order state machine. Administration and future workers must respect the same ownership boundaries. This is a code-level policy, not a claim of SQL permission isolation.

The design introduces no independently scalable domain storage and no new service. Enforcing boundaries remains implementation work.

## Reversibility

Moderate while interfaces are small; expensive if many callers later depend on direct persistence details.

## Reconsideration Trigger

Reconsider individual ownership assignments when validated use cases show misplaced responsibilities; do not relax all boundaries merely for convenience.

## Related Decisions

- [Database Engine](ADR-0008-database-engine.md).
- [Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).
- [Data architecture](../architecture/data-architecture.md).

## Notes

Read access, cross-module foreign keys, joins, exact table ownership and transaction boundaries remain pending. No blanket ban on foreign keys is implied. Framework-owned tables are technical data and require separate ownership conventions.
