# ADR-0010: Data Organization

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
| One database, shared application schema | Simple initial Django integration and local transactions | Shared resources and need to enforce module boundaries |
| One database, schema per module | Visible namespaces and potential schema grants | Extra schema/migration coordination; shared capacity and failure scope |
| Database per module | Independent data lifecycle and potential relocation | More connections, migrations, recovery and cross-database consistency work |

## Decision

Use one logical PostgreSQL database per environment, with one shared application schema for application tables.

## Approval

The project owner answered "lo recomendado" on 2026-09-28 after recommendations A for both data topology and write ownership. This record documents that explicit choice.

## Consequences

Orders and Inventory can participate in a local database transaction when business rules call for it. This enables atomicity but does not itself prevent overselling. Shared storage simplifies initial operation while retaining a shared logical recovery scope.

The design introduces no independently scalable domain storage and no new service. Enforcing boundaries remains implementation work.

## Reversibility

Moderately expensive to expensive to split later, depending on joins, constraints and workflows.

## Reconsideration Trigger

Reconsider when demonstrated isolation, ownership, recovery or scaling requirements outweigh migration and coordination costs.

## Related Decisions

- [Database Engine](ADR-0008-database-engine.md).
- [Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).
- [Data architecture](../architecture/data-architecture.md).

## Notes

Database/schema names, SQL roles, hosting, physical instance count, replicas, environment inventory, ORM policy and migration tooling remain pending. One logical database does not mean one physical server or no HA.
