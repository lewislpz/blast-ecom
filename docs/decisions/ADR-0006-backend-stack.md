# ADR-0006: Backend Stack

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
| Python + FastAPI | Explicit typed API and OpenAPI support | More integration choices for persistence and administration |
| Python + Django | Integrated ORM, migrations and administration | Framework conventions and coupling; API layer still to select |
| TypeScript + NestJS | Shared language with frontend and modular conventions | Node ecosystem and explicit persistence/admin integration |

## Decision

Use **Python + Django**.

Django supports the planned modular backend and provides integrated application facilities. The user selected Django after comparing all three options; this supersedes no Accepted ADR because the previous FastAPI recommendation was only a proposal.

## Approval

Project owner selected "1 B" in the explicit response "1 b / 2 a / 3 a" on 2026-09-28. This approves the named technologies, not implementation or unmentioned dependencies.

## Consequences

Django's conventions can reduce integration work, but domain workflows must not become implicit CRUD operations. Administrative writes must eventually enforce the same business rules as customer actions. API framework, persistence conventions, authentication, Django admin usage, versions and dependency tooling remain undecided.

No capacity or performance figures are assumed. Nothing is installed or deployed by this record.

## Reversibility

Expensive to reverse once models, migrations and API integrations accumulate.

## Reconsideration Trigger

Revisit if concrete requirements cannot be met reasonably with Django.

## Related Decisions

- [Application Architecture](ADR-0002-application-architecture.md).
- [Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).
- [Core stack and other ADRs](README.md).

## Notes

Versions will be selected after compatibility and support checks. See [project status](../project-status.md) for open decisions.
