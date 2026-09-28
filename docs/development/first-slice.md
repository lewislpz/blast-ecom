# First Implementation Slice

Status: Accepted target and acceptance criteria. The bounded implementation plan is approved and task task-1 is in progress; this specification alone is not verification evidence.

## Outcome

A local simulated purchase journey: fictional catalog → registered login → order with reservation → simulated payment outcome or cancellation → own order history. Django admin manages fictional catalog and audited stock adjustments. Browser interface clearly says simulation.

## Ordered Increments

1. Scaffold runtime/locks/config, custom user initial migration and real PostgreSQL connectivity; verify compatibility.
2. Catalog and inventory models/services, admin permissions and concurrency tests.
3. Order/reservation state machine, idempotency and payment simulator.
4. Session/CSRF API and generated OpenAPI, with high-risk security review before integration acceptance.
5. Customer React journey and generated types.
6. Restartable maintenance, audit/diagnostics, integration/E2E checks and updated docs.

Do not deliver all increments as one unreviewable code change. Dependency order may combine the custom user/schema scaffold before full authentication behavior.

## Acceptance Matrix

| Case | Expected result |
|---|---|
| Product CRUD by permitted staff | Customer sees only active catalog |
| Checkout with valid stock/prices | One awaiting_payment order and reservations |
| Successful simulation | confirmed, reserved consumed once, notification intent |
| Failed simulation | failed, reservation released once |
| Cancellation before payment/deadline | cancelled, release once |
| Expiry/restart | expired and released eventually; no late success |
| Other customer's UUID | 404; no leaked body |
| Repeat checkout key | Original response; no extra order |
| Changed payload under same key | 409 |
| Concurrent last unit | No negative availability or oversell |
| Price changed | Explicit conflict and reconfirmation |
| Staff generic edit | Cannot alter counters/state outside domain actions |
| Browser flow | Keyboard-accessible errors and no persistent credentials |
| Clean/upgrade DB | Migrations verified and no drift |
| Logs | Request correlation without credentials or addresses |

Remaining launch gates are in the decision register. Success of this slice is not a public-production readiness claim.
