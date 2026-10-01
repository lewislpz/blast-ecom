# ADR-0029: Public Account Security and Email Delivery Boundary

## Status

Accepted

## Date

2026-10-01

## Context

The local demo account flows use console email and permit sign-in before verification. A public customer flow must not treat developer-visible console output as proof of mailbox ownership, expose account existence, or accept forwarded source/protocol headers from arbitrary clients. Registration and reset also need durable delivery intent so a process interruption does not silently discard the request.

The user delegated remaining technical choices and implementation to Codex on 2026-10-01. This decision applies to the current modular-monolith implementation; it does not authorize enabling public accounts or claim a production deployment.

## Decision Drivers

- Preserve the current Django session, CSRF, PostgreSQL and modular-monolith design.
- Keep local demo behavior usable and clearly distinct from public behavior.
- Fail closed when non-debug security or mail configuration is unsafe.
- Avoid account enumeration and never persist one-time account tokens in the outbox.
- Make throttling effective across source addresses while retaining source-specific limits.
- Keep delivery provider details replaceable without introducing a broker prematurely.

## Options Considered

### Option A — Keep account flows local-only

Continue to use DEBUG-only registration, recovery and console email.

Advantages:

- No production configuration or asynchronous delivery code.
- Smallest operational footprint.

Disadvantages:

- Does not provide a path to safely test public-account behavior.
- Mailbox verification and verified-customer authorization remain unimplemented.

### Option B — Explicit public-account mode with Django SMTP and PostgreSQL outbox

Keep account routes disabled by default outside DEBUG. When explicitly enabled, require validated SMTP settings, queue minimal delivery intents transactionally in PostgreSQL, and process them with a bounded management command. Generate verification/reset tokens only at send time. Require verified email for customer login and checkout.

Advantages:

- Uses current framework/database and avoids a new broker or service.
- Persists delivery intent across application restarts.
- Keeps tokens out of durable queue records and logs.
- Local demo behavior remains separate.

Disadvantages:

- SMTP delivery is at-least-once; uncertain send outcomes can produce duplicate messages.
- The command still needs a supervised scheduler/worker in a hosted deployment.
- PostgreSQL counters and source limits are not an edge-level defense against distributed or volumetric attacks.
- Actual deliverability, sender-domain reputation, bounce processing and provider behavior require external validation.

### Option C — External identity and managed email platform

Delegate identity lifecycle and/or transactional mail to hosted providers.

Advantages:

- Potentially stronger managed security, delivery reporting and abuse controls.
- Can reduce application-owned credential and email operations.

Disadvantages:

- Provider selection, account setup, credentials, data processing and recovery become required.
- Adds external dependencies and integration work before hosted requirements are known.
- Cannot be verified in the current local environment.

## Decision

Use Option B. Public account flows are controlled by `BLAST_ECOM_PUBLIC_ACCOUNT_FLOWS_ENABLED` and remain disabled by default. Non-debug startup requires explicit public hosts/origins, a strong secret, HTTPS frontend/CSRF origins, HSTS and PostgreSQL `verify-full`; enabling account flows additionally requires an SMTP backend, credentials, a valid port, exactly one TLS mode and a non-local sender domain.

Only explicitly configured proxy CIDRs may supply forwarded client/protocol headers. Authentication limits add a global HMAC-pseudonymous identity bucket alongside per-source and source-plus-identity limits. Public registration, recovery and verification responses are generic; created accounts cannot log in or create orders before mailbox verification. The account email outbox stores only user, purpose and bounded retry state. Processing claims one row immediately before delivery with PostgreSQL row locking, retries with backoff and dead-letters after eight attempts. Tokens are generated only for delivery. Just-in-time claims avoid expiring leases for later messages during a slow sequential batch.

Local DEBUG flows retain console email and their demo semantics. This decision does not enable production routes, configure a delivery scheduler, or attest successful SMTP delivery or production readiness.

## Consequences

### Positive

- Public-account behavior has a testable, explicit trust boundary while local development remains simple.
- SMTP failure does not erase queued intent; retry state is durable and bounded.
- Email verification gates public customer access without changing local demo sign-in.

### Negative

- Operators must supervise the outbox command and monitor retry/dead-letter growth before enabling public flows.
- PostgreSQL becomes the shared coordination point for identity quotas and mail work.
- Generic SMTP is less capable than a dedicated email platform for bounces, complaints, reputation and delivery analytics.

### Risks

- Edge/shared rate controls, staff MFA, privacy retention/erasure, SMTP sender-domain validation and independent review remain launch gates.
- At-least-once delivery may send duplicates after a crash or ambiguous transport result for the current message.
- No hosted configuration or live SMTP test exists; the runtime flag must remain disabled until such a deployment is reviewed.

## Reversibility

Moderately expensive to reverse. The database-backed outbox and Django email boundary can be retained or replaced behind an adapter; changing identity ownership or token semantics would affect account lifecycle and requires migration and security review.

## Revisit When

- A hosted account, verified sender domain or managed identity/mail requirement is selected.
- Outbox volume, delivery reporting, bounce handling or independent scaling justifies a dedicated provider/queue.
- Edge/shared abuse controls, privacy policy, retention and staff MFA are defined for a public launch.

## Related Decisions

- [ADR-0016: Identity and Administration](ADR-0016-identity-and-administration.md)
- [ADR-0024: Authentication Attempt Limits](ADR-0024-authentication-attempt-limits.md)
- [ADR-0025: Local Account Recovery and Email Verification](ADR-0025-local-account-recovery-and-email-verification.md)
- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)
