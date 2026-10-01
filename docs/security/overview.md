# Security Baseline

Status: Local-development controls for catalog/admin permissions, customer session/CSRF/order APIs, Group administration, PostgreSQL-backed authentication limits, password recovery and demo email verification are implemented and tested. A separate, explicitly enabled public-account path now has fail-closed configuration, trusted-proxy parsing, cross-source identity limits, verified-email enforcement and a durable SMTP outbox; it remains disabled by default and is not production-approved. SMTP delivery, hosted worker supervision, edge abuse controls, staff MFA, privacy operations and independent review remain launch gates. [ADR-0016](../decisions/ADR-0016-identity-and-administration.md), [ADR-0023](../decisions/ADR-0023-break-glass-group-administration.md), [ADR-0024](../decisions/ADR-0024-authentication-attempt-limits.md), [ADR-0025](../decisions/ADR-0025-local-account-recovery-and-email-verification.md), [ADR-0029](../decisions/ADR-0029-public-account-security-and-email-delivery.md).

## Identity

Custom AbstractUser-based user from initial migration, username removed in favor of normalized email as login identifier. Normalize consistently (trim and lowercase under the selected product policy), validate syntax and enforce case-insensitive uniqueness in the database as well as application validation. Email case handling is a product convention, not a claim about all email providers.

Use Django's password hashing API/default supported PBKDF2 configuration and built-in common-password, similarity and numeric validators, with a 12-character minimum and 128-character input maximum. Never store/log plaintext passwords or implement cryptography. Exact hasher work factors track the selected patched Django release.

Registration creates a customer only; role/staff flags are not writable input. DEBUG enables the local console-email demo. Outside DEBUG, account flows remain unavailable unless `BLAST_ECOM_PUBLIC_ACCOUNT_FLOWS_ENABLED=true` is explicitly set and valid SMTP/security configuration is supplied. Public responses are generic, intents are queued transactionally, and unverified customers cannot sign in or create orders. See [authentication flows](authentication.md). Local verification does not prove control of a real mailbox; local tests do not validate external mail delivery.

## Sessions and Origin

Database-backed Django sessions; cookie HttpOnly, SameSite=Lax and Secure for HTTPS deployments. No JWT or localStorage credentials. Same-origin frontend/API/admin in deployed design; local Vite proxy handles /api and /admin with /static proxy for Django admin assets. Do not enable permissive credentialed CORS.

Customer sessions expire after 12 hours; staff after one hour, configured at login, with no indefinite sliding extension. These are provisional policy defaults. Django rotates session on login and logout flushes it. Successful local password reset changes the password hash without refreshing the current session-auth hash, invalidating existing sessions. Inactive users cannot authenticate.

CSRF token bootstrap endpoint, `X-CSRFToken` header for unsafe requests, and explicit CSRF enforcement on local registration/login as well as authenticated mutations/logout. DRF SessionAuthentication alone does not protect anonymous login views. The CSRF cookie is HttpOnly; clients obtain the request token from bootstrap JSON and refresh it after session rotation. Staff authorization and CSRF apply to admin/custom admin actions too.

## Authorization

| Actor | Allowed | Denied |
|---|---|---|
| Anonymous | Read active catalog; CSRF bootstrap; local auth initiation | Orders, inventory mutation, user enumeration |
| Active customer | Own checkout, order list/detail, own payable-order payment and cancellation | Other customers' orders; staff actions; setting price/status/owner |
| Staff with named permissions | Catalog management, audited stock adjustment, order inspection and explicit pending-order cancellation | Arbitrary state edits, silent stock overwrite, granting own privileges |
| Superuser | Bootstrap/break-glass only | Routine usage policy forbids treating it as normal staff |

Use Django groups and explicit permissions, not is_staff alone. The implemented catalog admin requires named model permissions; stock adjustment additionally requires `inventory.adjust_stock`. Superusers are deliberately excluded from routine catalog/inventory ModelAdmin operations. Order HTTP routes require an active non-staff customer and scope reads/mutations/replays to that owner. Same-user UUID knowledge does not grant access.

The built-in Group admin is replaced with a break-glass-only admin: every Group admin action requires an active staff superuser. Ordinary staff must not be able to edit a group's permissions, including a group they belong to. Regression tests cover both denial for ordinary staff and access for the break-glass superuser.

## Administration

Django admin is the initial internal UI; React remains the customer UI. Implemented catalog records can be managed only with explicit add/change/view permissions and cannot be deleted through admin. Stock counters are read-only in admin; stock changes use the transactional adjustment form and append actor, reason and delta. Order/payment/reservation fields and custom order actions remain planned. The stock counter and its adjustment audit record commit or roll back together.

## Secrets, Inputs and Exposure

Secrets/config via environment, ignored local env files and example placeholders only. Backend fails fast for missing required configuration. Never expose secrets through VITE_ variables. DEBUG disabled outside local tests; allowlisted hosts and trusted origins; parameterized ORM queries and plain-text descriptions (no arbitrary HTML).

Customer login and local registration use atomic PostgreSQL fixed-window counters keyed by HMAC-SHA-256 digests of source and (when available) normalized identity. Django Admin login shares the same policy. Current defaults are configurable and provisional: login 30/minute per source and 5/15 minutes per source+identity; local registration 10/hour per source and 3/hour per source+identity. Invalid CSRF requests do not consume quota. PostgreSQL failures fail closed. The cleanup runs only through the DEBUG/local-database maintenance command.

These app-level controls add HMAC-pseudonymous global identity quotas alongside per-source and source+identity counters. Forwarded client/protocol headers are honored only when the direct peer is in `BLAST_ECOM_TRUSTED_PROXY_CIDRS`; no proxy CIDRs are trusted by default. Misconfigured proxies, distributed account-targeted abuse, botnets and volumetric denial of service still require edge/shared controls and monitoring. Before public exposure, also require independently reviewed SMTP delivery, supervised outbox processing, staff MFA/access restrictions, privacy retention/erasure, TLS, and a CSP matching built assets. No public readiness is claimed.

## Sources

[Django sessions](https://docs.djangoproject.com/en/5.2/topics/http/sessions/), [custom users](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/), [password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/), [CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/), [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/).
