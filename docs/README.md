# Documentation

## Start Here

- [Project status](project-status.md)
- [Delegated decision report](reports/2026-09-28-phase0-decisions.md)
- [ADRs](decisions/README.md) and [decision register](roadmap/decision-register.md)
- [Roadmap](roadmap/roadmap.md)

## Product

[Overview](product/overview.md), [scope](product/scope.md), [actors](product/actors.md), [use cases](product/use-cases.md), [glossary](product/domain-glossary.md), [purchase workflow](product/purchase-workflow.md).

## Architecture

[Overview](architecture/overview.md), [principles](architecture/principles.md), [system context](architecture/system-context.md), [data architecture](architecture/data-architecture.md), [data model](architecture/data-model.md), [application structure](architecture/application-structure.md).

## API and Security

[HTTP standards](api/standards.md), [idempotency](api/idempotency.md), [security baseline](security/overview.md), [threat model](security/threat-model.md).

## Development and Operations

[Tooling](development/tooling.md), [local development](development/local-development.md), [frontend](development/frontend.md), [testing](development/testing-strategy.md), [migrations](development/migrations.md), [first implementation slice](development/first-slice.md), [backup and restore operations](operations/backups.md), [observability](operations/observability.md).

## State and Maintenance

Capabilities: Implemented, Planned, Proposed, Under discussion, Deprecated. Decision register: DECIDED, PROPOSED, UNDER DISCUSSION, DEFERRED, REJECTED. ADR states: Proposed, Accepted, Rejected, Superseded, Deprecated.

Accepted design does not mean implemented software. Prior ADRs preserve the facts/pending questions at their creation; active specifications and later ADRs refine them. No older choice is silently reversed. Replacements require linked Superseded/Accepted records.

ADR-0013 through ADR-0021 use the user's explicit delegation for that round, recorded as Codex decisions. ADR-0022 records the follow-up OpenAPI generator compatibility decision under the user's continuing implementation delegation. Update indexes, diagrams, status and affected specs in the same change. Avoid empty placeholders; infrastructure/runbooks wait for real subjects.
