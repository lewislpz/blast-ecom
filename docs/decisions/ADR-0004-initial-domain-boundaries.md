# ADR-0004: Initial Domain Boundaries

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is in Phase 0 without application implementation. This record captures initial discussion Decision 004.

## Decision Drivers

- Coherent, incrementally delivered v1.
- Clear responsibilities and maintainable documentation.
- Proportionate operational and development complexity.
- Preserve user control over significant choices.

## Options Considered

Six logical areas (Users, Products, Inventory, Orders, Payments, Notifications); four broader areas (Users, Catalog, Sales, Notifications).

| Option | Benefits | Costs and risks |
|---|---|---|
| Six areas | Explicit responsibilities and room to evolve ownership | More internal interfaces; risk of unnecessary abstractions |
| Four areas | Fewer initial boundaries and simpler coordination | Catalog/stock and orders/payments can become entangled; later separation costs more |

Neither option requires multiple deployments. Payments and Notifications may begin as small internal capabilities.

The tradeoffs were presented in the initial decision round and clarified before selection. The selected option's benefits and costs are recorded below. The other options remain available for future evaluation; not selecting them does not mark them permanently Rejected.

## Decision

Maintain six distinct logical areas: Users, Products, Inventory, Orders, Payments and Notifications. These are not six services, repositories or databases.

## Approval and Scope

Decision maker: project owner (user). On 2026-09-28 the user explicitly answered “1. b / 2. a / 3. a / 4. a”; this ADR records option A for Decision 004.

Approval covers this foundation only. It does not select a technology, database layout, communication mechanism, deployment platform, detailed business rule or the separately asked seller/goods/currency assumptions.

## Consequences

### Positive

Clear responsibility vocabulary and room to refine ownership independently.

### Negative

More internal boundaries to define and preserve.

### Risks

Over-structuring small capabilities or confusing logical separation with distributed deployment.

## Reversibility

Moderately expensive to reverse; cheaper before persistence and contracts become established.

## Reconsideration Trigger

Revisit when validated use cases show misplaced responsibility or recurring cross-boundary changes.

## Related Decisions

See the [ADR index](README.md) for the four decisions accepted together. Scope constrains architecture and domain refinement; repository topology does not determine runtime topology.

## Notes

This is an accepted target direction, not an implemented capability. Detailed scope and open questions are maintained in [project status](../project-status.md).
