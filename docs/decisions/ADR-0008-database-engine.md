# ADR-0008: Database Engine

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is in Phase 0 with an accepted modular monolith, monorepo and six logical domains. The core stack was presented as three separate questions.

## Decision Drivers

- Support the accepted store scope with proportionate complexity.
- Keep contracts and domain responsibilities clear.
- Make development and operation maintainable.
- Respect explicit user selection.

## Options Considered

| Option | Benefits | Costs |
|---|---|---|
| PostgreSQL | Transactional relational engine and integrity constraints | Requires migration, backup, connection and recovery management |
| MySQL with InnoDB | Viable transactional relational alternative | Different SQL/tooling; similar operational responsibilities |

## Decision

Use **PostgreSQL**.

The user selected PostgreSQL as the relational engine for the initial product. This is an engine decision only.

## Approval

Project owner selected "3 A" in the explicit response "1 b / 2 a / 3 a" on 2026-09-28. This approves the named technologies, not implementation or unmentioned dependencies.

## Consequences

Relations and constraints fit orders, order items and inventory, but transaction design still determines stock correctness. Hosting, versions, instance/database/schema count, ownership, identifiers, ORM policy and migrations remain undecided.

No capacity or performance figures are assumed. Nothing is installed or deployed by this record.

## Reversibility

Expensive to reverse once production data and database-specific behavior exist.

## Reconsideration Trigger

Revisit only for a demonstrated requirement or operational constraint outweighing migration costs.

## Related Decisions

- [Application Architecture](ADR-0002-application-architecture.md).
- [Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).
- [Core stack and other ADRs](README.md).

## Notes

Versions will be selected after compatibility and support checks. See [project status](../project-status.md) for open decisions.
