# ADR-0002: Application Architecture

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is in Phase 0 without application implementation. This record captures initial discussion Decision 002.

## Decision Drivers

- Coherent, incrementally delivered v1.
- Clear responsibilities and maintainable documentation.
- Proportionate operational and development complexity.
- Preserve user control over significant choices.

## Options Considered

Modular monolith; independently deployed microservices; a modular core with selected separate processors.

| Option | Benefits | Costs and risks |
|---|---|---|
| Modular monolith | Integrated changes and fewer operational units | Shared deployment, scaling and process failure scope |
| Microservices | Independent deployment and per-service scaling | Network failures, compatibility, data coordination and higher operational cost |
| Hybrid | Selective task isolation and scaling | Two execution models and remote failure handling; needs a specific reason to separate work |

The tradeoffs were presented in the initial decision round and clarified before selection. The selected option's benefits and costs are recorded below. The other options remain available for future evaluation; not selecting them does not mark them permanently Rejected.

## Decision

Start with a modular monolith: distinct business modules sharing the initial backend deployment.

## Approval and Scope

Decision maker: project owner (user). On 2026-09-28 the user explicitly answered “1. b / 2. a / 3. a / 4. a”; this ADR records option A for Decision 002.

Approval covers this foundation only. It does not select a technology, database layout, communication mechanism, deployment platform, detailed business rule or the separately asked seller/goods/currency assumptions.

## Consequences

### Positive

Fewer deployment units; easier integrated development and debugging.

### Negative

Shared release and scaling boundary; a process failure can affect multiple domains.

### Risks

Internal coupling could make future extraction expensive. Distribution still needs deliberate contract and consistency design if introduced later.

## Reversibility

Moderately expensive to expensive to reverse, depending on data coupling and remote contracts.

## Reconsideration Trigger

Revisit when measured scaling, failure isolation or team deployment autonomy justifies distribution.

## Related Decisions

See the [ADR index](README.md) for the four decisions accepted together. Scope constrains architecture and domain refinement; repository topology does not determine runtime topology.

## Notes

This is an accepted target direction, not an implemented capability. Detailed scope and open questions are maintained in [project status](../project-status.md).
