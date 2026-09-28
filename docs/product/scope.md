# V1 Scope

Status: Accepted target, not implemented. ADR-0001 establishes the intermediate store; ADR-0013 through ADR-0021 refine behavior under delegated authority.

## Included

- React customer interface and restricted Django admin.
- Registered customer checkout, session authentication and own order history.
- Public active products/categories; simple product fields and static image references.
- Single logical stock pool, audited adjustments, reservation/consumption/release.
- awaiting_payment, confirmed, failed, cancelled and expired orders.
- Cancellation only before successful payment and before reservation deadline.
- One deterministic simulated payment attempt per order.
- Durable simulated notification intent and maintenance processing.
- Temporary browser cart without persistence.
- Delivery-address snapshot, explicitly simulated shipping and no tax-invoice claim.

Commerce model remains one seller, physical products, EUR. See [workflow](purchase-workflow.md) for invariants and provisional defaults.

## Outside v1 Baseline

Guest checkout, variants, persistent cart, advanced search, marketplace, multiple currencies/warehouses, real payment, refunds/post-payment cancellation, fulfillment tracking and external notification delivery.

## Real-Launch Gates

Destination markets, actual taxes/invoicing, shipping charges/coverage, email verification/delivery, privacy retention and public security/operation requirements remain deferred. Local simulation defaults are not legal/commercial decisions.

## Delivery

The [first slice](../development/first-slice.md) defines small ordered increments. No implementation is performed or authorized by recording this design. Production readiness is separate from functional completeness.
