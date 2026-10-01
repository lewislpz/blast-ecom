# ADR-0025: Local Account Recovery and Email Verification

## Status

Accepted

## Date

2026-10-01

## Context

The local-only account flow had no password recovery and no way to exercise email verification. Public registration, external delivery and production account ownership remain explicitly out of scope. New auth flows add sensitive unauthenticated endpoints and must not weaken generic errors, CSRF, password policy or existing customer sessions.

## Decision Drivers

- Make account recovery and verification testable in local development without provider credentials.
- Prevent reset-request responses from disclosing whether an eligible account exists.
- Use framework-maintained one-use password reset semantics rather than custom cryptography.
- Preserve access for existing demo accounts and avoid asserting that console output proves control of a real mailbox.
- Keep public registration and recovery disabled outside `DEBUG=true`.

## Options Considered

### Option A — Django console email and built-in reset token generator

Send local messages through Django's console backend; verify reset tokens using Django's built-in password reset token generator and verify local-email tokens using Django's timestamped signing utilities.

Advantages:

- No provider account, network delivery, secrets or new dependency.
- Password tokens are tied to user password state and become unusable after a successful reset.
- Local developers can exercise real UI/API workflows by opening the generated local link.

Disadvantages:

- Console output is not delivery to an actual mailbox and cannot prove mailbox ownership.
- DEBUG-only recovery is not a production customer-support solution.

### Option B — Add a real email provider now

Configure SMTP or a transactional email API and deliver verification/reset messages externally.

Advantages:

- Tests a real outbound delivery boundary and can verify control of a real mailbox.

Disadvantages:

- Requires provider, credentials, DNS/domain, deliverability, privacy and operational decisions not available for this local-development milestone.
- Adds external network, cost and secret-management risks.

### Option C — Omit verification state until public launch

Keep current login and implement password recovery only.

Advantages:

- Smallest immediate data/API change.

Disadvantages:

- Leaves the requested local verification journey untestable and delays learning about verification UX.
- A future implementation would still need migration and UI/API contract work.

## Decision

Use Option A for local development. Configure Django's console email backend; never return tokens in API responses or application logs. The intended local email message is the only place where developers can see a link/token. Password reset uses Django's default one-use token generator, a one-hour timeout, CSRF-protected POST confirmation, the existing password validators, and the user row lock so concurrent replays cannot both succeed. Change the password without refreshing the current session-auth hash so existing sessions are invalidated.

Store nullable `email_verified_at`; do not backfill historical users as verified. New local registrations receive a signed, one-hour verification link. A valid link marks the local account once. Verification is informational only in this demo: unverified existing/new local customers can still log in. Console output and the verification timestamp do not prove possession of an external mailbox. Registration, reset request, reset confirmation, verification request and verification confirmation are DEBUG-only. Recovery request responses are generic for missing, staff, inactive and eligible accounts. Requests and confirmation attempts are bounded by the existing PostgreSQL-backed throttle mechanism.

This bounded choice is made under the user's explicit 2026-10-01 instruction to complete the previously identified local-development items autonomously. It does not authorize public account launch, external email delivery, deployment or production ownership claims.

## Consequences

### Positive

- Local developers can exercise reset and verification from registration through UI/API.
- Existing accounts remain usable and are not incorrectly marked verified.
- Reset request responses do not identify eligible accounts.
- Tokens are absent from API responses and application logs; the local console email intentionally exposes links for manual development use. Token values are submitted in POST bodies after the UI removes them from the URL fragment.

### Negative

- Console email requires developers to copy/open links manually.
- Verification state is not an authentication or authorization control.
- Email sending failure is intentionally silent to preserve generic recovery responses; local console output must be checked during development.

### Risks

- A future deployment could mistakenly treat local verification as proof of mailbox ownership. Production must replace the flow with verified provider delivery, ownership/abuse controls, privacy retention, trusted proxy handling and review.
- Password recovery in DEBUG mode should only be reachable from trusted local development and disposable demo data.
- Response status/body do not reveal account eligibility, but console email generation can still create timing differences; DEBUG-only local access is a scope boundary, not public anti-enumeration assurance.
- App-level throttles do not protect against distributed or volumetric attacks.

## Reversibility

Moderately expensive to reverse: route/UI behavior and an additive nullable user column can be removed, but tokens and API consumers must be migrated deliberately.

## Reconsideration Trigger

Before enabling registration/recovery outside DEBUG, before real customer data, or when external mailbox ownership must be established.

## Related Decisions

- [ADR-0016: Identity and Administration](ADR-0016-identity-and-administration.md)
- [ADR-0024: Authentication Attempt Limits](ADR-0024-authentication-attempt-limits.md)
- [Authentication security overview](../security/overview.md)
- [Authentication flows](../security/authentication.md)

## References

- [Django authentication and password reset](https://docs.djangoproject.com/en/5.2/topics/auth/default/)
- [Django cryptographic signing](https://docs.djangoproject.com/en/5.2/topics/signing/)
