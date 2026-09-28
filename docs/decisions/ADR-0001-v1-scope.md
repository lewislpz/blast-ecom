# ADR-0001: V1 Scope

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is in Phase 0 without application implementation. This record captures initial discussion Decision 001.

## Decision Drivers

- Coherent, incrementally delivered v1.
- Clear responsibilities and maintainable documentation.
- Proportionate operational and development complexity.
- Preserve user control over significant choices.

## Options Considered

A minimal API-oriented core; an intermediate usable store; a broader store with variants, persistent cart and fulfillment/refund simulation.

| Option | Benefits | Costs and risks |
|---|---|---|
| Minimal | Fast core validation with fewer interactions | No customer-facing store; important journeys remain unexplored |
| Intermediate | Usable purchase/admin journey and meaningful failure cases | More UI work, states and tests; requires scope discipline |
| Broader | Richer shopping experience | More integration and maintenance work before validating the core |

The tradeoffs were presented in the initial decision round and clarified before selection. The selected option's benefits and costs are recorded below. The other options remain available for future evaluation; not selecting them does not mark them permanently Rejected.

## Decision

Choose an intermediate usable store: customer/admin interfaces, catalog, stock, orders and history, reservations/release, cancellation, simulated payments and simulated notifications.

## Approval and Scope

Decision maker: project owner (user). On 2026-09-28 the user explicitly answered “1. b / 2. a / 3. a / 4. a”; this ADR records option B for Decision 001.

Approval covers this foundation only. It does not select a technology, database layout, communication mechanism, deployment platform, detailed business rule or the separately asked seller/goods/currency assumptions.

## Consequences

### Positive

A complete purchase journey; coherent scope for domain analysis.

### Negative

More rules and interaction states than an API-only increment; frontend and administration work.

### Risks

Scope expansion and premature implementation before product rules are defined.

## Reversibility

Moderately expensive to reverse once public behavior and persistent data exist.

## Reconsideration Trigger

Revisit if customer needs, capacity or release objectives materially change.

## Related Decisions

See the [ADR index](README.md) for the four decisions accepted together. Scope constrains architecture and domain refinement; repository topology does not determine runtime topology.

## Notes

This is an accepted target direction, not an implemented capability. Detailed scope and open questions are maintained in [project status](../project-status.md).
