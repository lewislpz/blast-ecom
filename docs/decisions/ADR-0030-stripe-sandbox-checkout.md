# ADR-0030: Stripe Sandbox Checkout and Manual Capture

## Status

Accepted

## Date

2026-10-01

## Context

Blast Ecom currently uses a local payment simulator. The production-readiness
increment needs a provider-backed sandbox without exposing card data to Blast Ecom,
trusting browser redirects, or capturing funds before the application has verified
that the order and stock reservation are still valid.

Stripe Checkout provides a hosted payment page. A Checkout Session can be created
server-side from the order's immutable line snapshots and can use the PaymentIntent
manual-capture option. Stripe's documented Checkout expiry has a 30-minute minimum;
the current local reservation deadline is 15 minutes. Webhook processing must therefore
handle a payment authorization arriving after the order expired, and must not capture
that authorization.

## Decision Drivers

- Keep card data out of Blast Ecom's frontend, API, logs and database.
- Keep order amount, currency and item snapshots authoritative on the server.
- Treat provider webhooks, not return-page navigation, as payment authority.
- Capture only after a valid provider authorization matches a payable order and active
  reservation.
- Keep network calls outside PostgreSQL transactions.
- Preserve the local simulator only for DEBUG development.
- Restrict this increment to provider sandbox credentials; no live payments.

## Options Considered

### Option A — Keep the deterministic simulator

Advantages:

- No external account, credentials or provider dependency.
- Existing local flow remains simple and deterministic.

Disadvantages:

- Does not exercise a real provider contract, hosted checkout, signatures or settlement
  lifecycle.
- Cannot meet sandbox integration acceptance criteria.

### Option B — Stripe-hosted Checkout with automatic capture

Advantages:

- Provider-hosted card collection keeps card entry outside Blast Ecom.
- Small frontend and operational footprint.
- Customer must explicitly submit the hosted Checkout form.

Disadvantages:

- The provider captures funds before Blast Ecom reconciles the order webhook.
- Delayed webhook delivery can leave a captured payment for an expired or cancelled
  order, requiring a refund workflow.
- Checkout's minimum session lifetime exceeds the current stock reservation TTL.

### Option C — Stripe-hosted Checkout with manual capture

Advantages:

- Card data remains on Stripe-hosted Checkout.
- The customer explicitly submits Checkout before Stripe authorizes the payment.
- Authorization and capture are separate; Blast Ecom can validate order state, amount,
  currency and reservation before capture.
- Late authorization for an expired/cancelled order can be cancelled rather than
  captured.

Disadvantages:

- Requires a durable, retryable capture workflow and explicit order/payment processing
  states.
- Manual capture is not available for every payment method, so this increment is
  restricted to card payments.
- A temporary authorization may remain visible to a customer when provider events are
  delayed, even though Blast Ecom will not capture it.

### Option D — Direct PaymentIntent with Stripe Elements

Advantages:

- More control over payment UX and payment-intent lifecycle.
- Card details are tokenized in Stripe Elements and need not reach Blast Ecom.

Disadvantages:

- Adds frontend SDK, client-secret handling and custom checkout UI complexity.
- No v1 product requirement justifies a custom card form over hosted Checkout.

## Decision

Use Stripe-hosted Checkout in sandbox mode with one Checkout Session per order payment
attempt, card payment methods only, and manual capture. Generate line items from the
server-owned order snapshots. Use a stable provider idempotency key derived from the
local payment attempt. Reconcile signed provider events using a unique event ID and
server-side state validation. A browser return URL is informational only.

Under the owner's explicit 2026-10-01 delegation to advance recommended implementation
decisions without pausing for individual choices, this decision is accepted for the
sandbox increment. This does not authorize live charges, external publication, or
production deployment.

## Consequences

### Positive

- Local development retains a deterministic simulator while non-debug runtimes cannot
  use it.
- Card details are entered on Stripe's hosted page, not Blast Ecom.
- A payment capture can be conditioned on a locked, still-payable order and active stock
  reservation.
- Retries can use provider idempotency and durable webhook receipts.

### Negative

- The payment workflow is more complex than automatic capture and requires explicit
  recovery behavior for authorization, capture and webhook retries.
- Sandbox use requires provider credentials and a registered webhook secret.
- The customer may see a pending authorization while an event is being reconciled.

### Risks

- Real Stripe sandbox acceptance cannot be claimed without a sandbox account and test
  credentials. Automated signed-event tests prove local verification logic only.
- A payment authorization can arrive after local order expiry because Checkout Session
  expiry cannot be shorter than 30 minutes. Such authorizations must be cancelled and
  never captured.
- Hosted operations, webhook delivery monitoring and provider reconciliation remain
  launch gates.

## Related Decisions

- [ADR-0014: Order and Reservation Lifecycle](ADR-0014-order-reservation-lifecycle.md)
- [ADR-0017: HTTP Contract and Idempotency](ADR-0017-http-api-contract.md)

## Notes

Official references reviewed on 2026-10-01:

- [Create a Checkout Session](https://docs.stripe.com/api/checkout/sessions/create)
- [Checkout Sessions API](https://docs.stripe.com/api/checkout/sessions)
- [Capture a PaymentIntent](https://docs.stripe.com/api/payment_intents/capture)
- [Stripe testing](https://docs.stripe.com/testing)
- [stripe-python releases](https://github.com/stripe/stripe-python/releases)
