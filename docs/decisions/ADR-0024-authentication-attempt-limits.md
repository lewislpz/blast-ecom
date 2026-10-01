# ADR-0024: Authentication Attempt Limits

## Status

Accepted

## Date

2026-10-01

## Context

Customer login, local-only registration, and Django Admin login had no shared attempt limits. A process-local or cache-based counter would not be atomic across workers and there is no cache service in the accepted local architecture. Authentication abuse controls are needed even for local integration testing, but must not imply public-service protection.

## Decision Drivers

- Limit common single-source password guessing and registration bursts.
- Share state across application processes without adding Redis.
- Avoid persisting raw email addresses or IP addresses.
- Preserve CSRF validation, generic credential failures, and fail-closed behavior.
- Keep local operations restartable and bounded.

## Options Considered

### Django REST Framework cache throttling

Use built-in scoped throttles and the configured Django cache.

Advantages:

- Minimal implementation and idiomatic API integration.
- Suitable for general application overuse policy.

Disadvantages:

- Depends on cache configuration and may be process-local.
- Counters are not atomic under concurrency; this does not meet the abuse-control objective.
- Django REST Framework explicitly warns that its throttles are not a security measure against brute-force or denial-of-service attacks.

### Redis-backed counters

Add Redis for atomic, shared counter operations.

Advantages:

- Shared state with suitable atomic primitives.
- Could support broader ephemeral-state use cases later.

Disadvantages:

- Adds a service, availability dependency, operational setup, and failure behavior without a current broader Redis requirement.

### PostgreSQL atomic counters

Use one atomic upsert per counter in the existing database, keyed by an HMAC digest.

Advantages:

- Shared across app processes and atomic under PostgreSQL concurrency.
- Requires no additional service.
- HMAC digests avoid storing raw source or identity values.

Disadvantages:

- Adds writes to the main database and a table requiring cleanup.
- Database failure denies authentication mutations rather than bypassing the control.
- App-level source controls do not stop distributed or volumetric attacks.

## Decision

Use PostgreSQL atomic fixed-window counters with HMAC-SHA-256 keys derived from `SECRET_KEY`. Each customer/admin login request consumes a source counter and, when a normalized identity is available, a source+identity counter. Local registration has a separate policy. Count every CSRF-valid attempt before credential/account validation; invalid CSRF requests do not consume quota.

Initial configurable defaults:

- Customer and Django Admin login: 30 attempts/minute per source; 5 attempts/15 minutes per source+identity.
- Local DEBUG-only registration: 10 attempts/hour per source; 3 attempts/hour per source+identity.

Denied customer API requests return generic RFC 9457 Problem Details with HTTP 429, `RATE_LIMITED`, and `Retry-After`. Admin receives a generic 429 page. PostgreSQL errors fail closed through the generic 503 handler. Bounded expiry cleanup runs in the existing DEBUG/local-database maintenance command. Only `REMOTE_ADDR` is trusted; forwarded client headers remain ignored until a trusted proxy topology exists.

This is an app-level local-development control. Before public exposure, configure trusted proxy parsing, edge/shared abuse controls, monitoring, staff MFA/access policy, and email ownership flows.

This decision was made under the owner's explicit instruction to continue autonomously, make recommended decisions, and complete the application. It is limited to this bounded implementation decision and does not authorize cloud spending or deployment.

## Consequences

### Positive

- Attempts are shared across application workers and increments are atomic.
- Identity and source values are not stored in plaintext or returned to clients.
- No cache service is added solely for throttling.
- Customer API, local registration and staff admin login share a documented policy.

### Negative

- Authentication attempts add up to two database writes.
- A PostgreSQL outage prevents these authentication mutations.
- Defaults are provisional and have not been capacity-tuned.

### Risks

- Distributed clients can evade per-source limits.
- Incorrect proxy configuration can misidentify clients; forwarded headers are intentionally not trusted yet.
- This control does not protect the database or upstream network from volumetric denial of service.

## Reversibility

Moderately expensive to reverse: the table and implementation can be removed with a migration, but operational policy and API 429 behavior should remain when replaced.

## Reconsideration Trigger

Revisit before any shared/public deployment, or if measured database load or broader ephemeral-state needs justify adopting a shared edge service or cache.

## Related Decisions

- [ADR-0016: Identity and Administration](ADR-0016-identity-and-administration.md)
- [ADR-0021: Operations Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)
- [Security overview](../security/overview.md)
- [Initial threat model](../security/threat-model.md)

## References

- [Django REST Framework throttling guidance](https://www.django-rest-framework.org/api-guide/throttling/)
