# ADR-0005: Initial Commerce Model

## Status

Accepted

## Date

2026-09-28

## Context

The intermediate v1 scope left seller model, goods type and currency unresolved. These choices constrain catalog, inventory and purchase workflows.

## Decision Drivers

- Keep the first usable store bounded.
- Model physical stock consistently.
- Avoid unnecessary seller and currency coordination.

## Options Considered

| Choice | Alternatives | Benefits and costs |
|---|---|---|
| Seller model | Single seller; marketplace | A single seller simplifies ownership and administration. A marketplace supports multiple sellers but adds seller isolation and operational coordination. |
| Goods | Physical; digital; both | Physical goods align with stock reservations but require delivery rules later. Digital goods require access/delivery rules. Both require distinct workflows. |
| Currency | EUR only; another single currency; multiple currencies | One currency avoids conversion policy. Multiple currencies broaden purchasing options but add price, conversion and rounding rules. |

## Decision

- One store operated by a single seller.
- Physical products in v1.
- EUR as the sole v1 transaction currency.

## Approval

The project owner explicitly selected "1 a / 2 a / 3 a" on 2026-09-28 after these alternatives were presented. Each selection is recorded above; the subsequent request to decide the stack does not itself approve a technology.

## Consequences

### Positive

The initial domain does not require seller tenancy, digital entitlement delivery or currency conversion.

### Negative

Multi-seller operations, digital product sales and transactions in other currencies are outside the accepted v1 model.

### Risks

Physical goods still require explicit address, shipping and tax treatment before checkout is implemented. EUR alone does not determine jurisdiction, tax rules or language. One seller does not mean one administrator or one warehouse.

## Reversibility

Moderately expensive to expensive after data and contracts exist: adding sellers changes ownership; digital goods change fulfillment; multiple currencies change price and order semantics. No migration is needed at the current documentation-only stage.

## Reconsideration Trigger

Explicit product requirements for additional sellers, digital goods or other currencies.

## Related Decisions

- [ADR-0001: V1 Scope](ADR-0001-v1-scope.md) — refined, not replaced.
- [ADR-0004: Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).

## Notes

No schema, monetary representation, tax engine, warehouse topology or logistics integration is selected here.
