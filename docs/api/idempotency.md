# Idempotency

Status: Accepted design, not implemented. Applies to order creation, payment and cancellation.

## Key and Scope

Require a client-generated UUIDv4 Idempotency-Key; scope by authenticated user, route operation and key. The fingerprint covers validated canonical JSON and path target, including expected prices/address; never authentication secrets. Enforce a unique database constraint and compare the fingerprint before effects.

The frontend creates a key once per user action and retains it across retries of that action. Changing payload starts a new action/key. Never retry mutations with a newly generated key automatically.

## Atomic Processing

Insert or lock the scoped IdempotencyRecord within the operation transaction before business locks. Handle a competing unique insert with a savepoint/reselect (not further queries inside a broken transaction). Same key/fingerprint waits for the committed result and replays stored status/body. Different fingerprint returns 409 IDEMPOTENCY_CONFLICT.

Business writes and stored successful/domain-conflict result commit together. Unexpected failure rolls back both; retry with the same key can execute again safely. Authentication, CSRF and syntax validation failures happen before key creation and are not cached. Existing-resource authorization is rechecked before replay. Do not recreate a cancelled/expired order just because a create response is replayed.

Payment failure is a committed 200 domain result. Expiry detected during payment/cancel is a committed expiry/release with stored 409 ORDER_EXPIRED, not an exception that accidentally rolls the release back.

## Lifetime and Races

Retain completed records at least 24 hours as an explicit provisional retry window. Keys are opaque references and fingerprints/results may contain personal data: restrict access, never log bodies, delete completed expired records through maintenance. Cleanup locks the record and rechecks expiry before removal. After retention, reuse may create a new operation; clients must never intentionally reuse old keys.

Order-level terminal state and one-payment-attempt constraints still prevent duplicate payment effects even with different keys. Creating a genuinely new key can create another order; the UI must prevent accidental double submission and show the existing order after an uncertain response.

On connection loss, the client cannot infer rollback; retry same key. If a response is replayed, request_id may be the original stored response ID and an additional current X-Request-ID may identify the retry; do not use request IDs as idempotency keys.
