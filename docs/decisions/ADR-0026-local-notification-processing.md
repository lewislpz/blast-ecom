# ADR-0026: Restart-Safe Local Notification Processing

## Status

Accepted

## Date

2026-10-01

## Context

Order transitions create durable notification intents in the same database transaction as the transition. Local development needs a bounded processor that survives process restarts without introducing a broker or a third-party delivery provider. The local email backend is a simulation, not customer email delivery.

## Decision Drivers

- A failed attempt must remain visible and retryable.
- Processing must be bounded and safe with multiple local workers.
- Notification failures must not roll back committed order state.
- No external provider or broker is justified for the current local scope.
- This behavior must not be exposed as production delivery.

## Options Considered

### Option A — Durable database intent with local console delivery

Claim pending intents in a short bounded batch using row locks, render through Django's configured local console backend, and mark successful intents simulated. On failure, retain pending state and record attempt metadata. Prioritize never-attempted work before retries.

Advantages:

- Uses the existing database and maintenance process.
- Survives process restart; row locks prevent concurrent workers claiming the same intent.
- No broker/provider operations or credentials.

Disadvantages:

- A console write can happen immediately before a database commit failure; a subsequent retry can print it again (at-least-once output).
- No external delivery, backoff scheduler, dead-letter queue, or operator alerting.

### Option B — Add a message broker

Publish notification jobs to a broker and process them asynchronously.

Advantages:

- More independent worker scaling and richer retry/routing options.

Disadvantages:

- Adds infrastructure and delivery/transaction coordination before the local workload needs it.
- Does not itself eliminate duplicate delivery or replace idempotency.

## Decision

Use Option A for local development. The processor is DEBUG-only, bounded to 1–1000 records per invocation, and uses `select_for_update(skip_locked=True)`. Failures remain pending with attempt count, timestamp, and exception class only. The console output is at-least-once in the narrow crash window described above; order state is never reverted because notification output failed.

## Consequences

### Positive

- Local intent processing is restart-safe and concurrent passes do not claim the same pending row.
- Failure state survives the process and can be retried on the next maintenance pass.
- Untouched work is prioritized over previously attempted failures.

### Negative

- Console output is not an exactly-once external side effect.
- Persistent failures have no automated backoff or terminal alert in the local scope.

### Risks

- Operators may mistake a printed console message for real delivery; docs and message content explicitly identify it as a local simulation.
- A poison intent can continue retrying; current local maintenance reports failures and preserves the intent for diagnosis.

## Related Decisions

- [ADR-0014: Order and Reservation Lifecycle](ADR-0014-order-reservation-lifecycle.md)
- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)

## Notes

Reconsider a broker/provider only when independently scalable delivery, actual external notifications, or operational retry/dead-letter requirements are approved.
