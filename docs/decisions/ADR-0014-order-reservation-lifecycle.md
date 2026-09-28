# ADR-0014: Order and Reservation Lifecycle

## Status

Accepted

## Date

2026-09-28

## Context

Orders, stock reservations, simulated payments and cancellation need a consistent failure model.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Local transactions and explicit operations | Strong consistency with the accepted shared database | Shared locking and synchronous work |
| Broker-driven saga from the start | Independent processing | Compensation, duplicate delivery and operational cost without external payment needs |

## Decision

Create an awaiting_payment order and all its reservations in one PostgreSQL transaction. Resolve its single simulated payment attempt in another transaction: success confirms the order and consumes reserved stock; failure marks it failed and releases stock. Customers can cancel only awaiting_payment orders. Expiry transitions them to expired. Confirmed orders are final for the v1 payment/reservation workflow, not shipped.

Use a configurable 15-minute reservation deadline as an explicit initial UX assumption. Check it under the order lock at every payment/cancellation attempt, not only in a scheduler. A restartable Django maintenance command sweeps expired orders and pending simulated notifications every 60 seconds in local development. It uses the same codebase and domain operations, not a broker or independent service. On failure, roll back and retry via the maintenance cycle. No network calls inside transactions. Failed/expired/cancelled orders require a new checkout; refunds/post-payment cancellation are deferred.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: A stopped maintenance process can temporarily hide available stock; deadlines still prevent late payment success. Paid cancellation is outside v1 and must be visible in UX.

## Reversibility

Moderate; distributed/external payment integration requires a new decision before replacing local atomic behavior.

## Reconsideration Trigger

External payment integration, delayed processing or measured worker isolation needs.

## Related Decisions and Specifications

- [purchase-workflow](../product/purchase-workflow.md).
- [data-architecture](../architecture/data-architecture.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
