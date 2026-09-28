# ADR-0012: Persistence Tooling

## Status

Accepted

## Date

2026-09-28

## Context

The accepted Django/DRF modular monolith uses PostgreSQL, a shared application schema and module-controlled writes. ORM and migration tooling remained undecided.

## Decision Drivers

- Integrate persistence with the selected framework.
- Minimize unnecessary maintenance and transaction coordination.
- Keep schema changes versioned and reviewable.

## Options Considered

| Option | Benefits | Costs and risks |
|---|---|---|
| Django ORM and Django migrations | Native model integration and one framework-aligned migration mechanism | Framework coupling; generated queries and migrations still need review |
| SQLAlchemy and Alembic for business data | Persistence can be less coupled to Django | Additional session/transaction integration; Django components may still need their own ORM and migration history |

## Decision

Use **Django ORM** for application persistence and **Django migrations** for versioned schema evolution. Do not introduce SQLAlchemy or Alembic for the initial application.

## Approval

On 2026-09-28 the project owner answered "lo que tu recomiendes" after recommendation A was explicitly presented as Django ORM plus Django migrations. This is approval of this bounded choice, not general permission to make subsequent architectural decisions.

## Consequences

### Positive

Persistence uses Django's integrated facilities and avoids maintaining a second ORM/migration mechanism.

### Negative

Models and queries become coupled to Django. Migration histories require maintenance and review.

### Risks

Generated SQL can be inefficient; migrations can lock tables or lose data if designed incorrectly. ORM use does not guarantee stock correctness or enforce module ownership. No performance or capacity guarantee follows from this choice.

## Reversibility

Expensive once models, queries and migration history accumulate. Explicit business boundaries reduce the affected scope but do not remove migration cost.

## Reconsideration Trigger

Demonstrated persistence requirements or framework separation needs that justify an alternative and its integration costs.

## Related Decisions

- [Backend Stack](ADR-0006-backend-stack.md).
- [Database Engine](ADR-0008-database-engine.md).
- [Data Organization](ADR-0010-data-organization.md).
- [Module Data Ownership](ADR-0011-module-data-ownership.md).

## Notes

Versions, model layout, identifiers, driver selection, transaction boundaries, migration execution ownership/timing, compatibility, rollback and destructive-change procedures remain pending. No models or migrations are implemented.

References consulted during comparison: [Django models](https://docs.djangoproject.com/en/5.2/topics/db/models/), [Django migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/), [SQLAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/en/latest/). Reference documentation versions do not select runtime versions.
