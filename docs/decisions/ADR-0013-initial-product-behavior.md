# ADR-0013: Initial Product Behavior

## Status

Accepted

## Date

2026-09-28

## Context

The accepted physical-goods store needs concrete behavior without inventing a tax jurisdiction or shipping provider.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Registered checkout, one stock pool | Clear ownership and bounded inventory | Account friction; simpler than guest/multiwarehouse flows |
| Guest checkout and multiple warehouses | Broader commercial support | More identity, merging and fulfillment rules |

## Decision

Use public catalog browsing, registered-customer checkout, one logical stock pool and a non-persistent browser cart. Use simple products with unique SKU, title, description, positive EUR price, active flag and one category; optional static bundled image references, no upload subsystem initially. Archive products instead of deleting referenced records.

Collect a delivery-address snapshot on the order. Initial development uses synthetic addresses, configured gross display prices, zero simulated shipping charge and no inferred tax rate, invoice or fulfillment claim. These are simulation defaults, not accepted real-world fiscal rules. Real sales remain gated on destination markets, tax and shipping requirements. Prioritize correctness, security and maintainability, then operability and user responsiveness; no arbitrary SLO or throughput target.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: Registered checkout can reduce conversion; synthetic shipping/tax behavior cannot be used for real trade.

## Reversibility

Moderate after customers/order data exist; easy before implementation.

## Reconsideration Trigger

Guest checkout demand, physical warehouse integration or a real-sales launch.

## Related Decisions and Specifications

- [purchase-workflow](../product/purchase-workflow.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
