# ADR-0003: Repository Strategy

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is in Phase 0 without application implementation. This record captures initial discussion Decision 003.

## Decision Drivers

- Coherent, incrementally delivered v1.
- Clear responsibilities and maintainable documentation.
- Proportionate operational and development complexity.
- Preserve user control over significant choices.

## Options Considered

Monorepo containing application and docs; multiple repositories with separate lifecycle and access.

| Option | Benefits | Costs and risks |
|---|---|---|
| Monorepo | Atomic cross-component changes and centralized documentation | Broad access and growing build coordination; accidental coupling |
| Multirepo | Separate permissions, ownership and lifecycle | Cross-repository version coordination and duplicated maintenance |

Neither option determines runtime performance or whether the application uses microservices.

The tradeoffs were presented in the initial decision round and clarified before selection. The selected option's benefits and costs are recorded below. The other options remain available for future evaluation; not selecting them does not mark them permanently Rejected.

## Decision

Use a monorepo for Blast Ecom application code and documentation.

## Approval and Scope

Decision maker: project owner (user). On 2026-09-28 the user explicitly answered “1. b / 2. a / 3. a / 4. a”; this ADR records option A for Decision 003.

Approval covers this foundation only. It does not select a technology, database layout, communication mechanism, deployment platform, detailed business rule or the separately asked seller/goods/currency assumptions.

## Consequences

### Positive

Coordinated changes and reviews; documentation close to implementation.

### Negative

Repository-wide access and build coordination need attention as the project grows.

### Risks

Accidental dependencies and overly broad tooling could reduce maintainability.

## Reversibility

Moderately expensive to reverse once history, dependencies and automation accumulate.

## Reconsideration Trigger

Revisit when independent access controls or ownership cannot be supported reasonably within one repository.

## Related Decisions

See the [ADR index](README.md) for the four decisions accepted together. Scope constrains architecture and domain refinement; repository topology does not determine runtime topology.

## Notes

This is an accepted target direction, not an implemented capability. Detailed scope and open questions are maintained in [project status](../project-status.md).
