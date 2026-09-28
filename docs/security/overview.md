# Security Baseline

Status: Accepted design, not implemented or audited runtime. [ADR-0016](../decisions/ADR-0016-identity-and-administration.md).

## Identity

Custom AbstractUser-based user from initial migration, username removed in favor of normalized email as login identifier. Normalize consistently (trim and lowercase under the selected product policy), validate syntax and enforce case-insensitive uniqueness in the database as well as application validation. Email case handling is a product convention, not a claim about all email providers.

Use Django's password hashing API/default supported PBKDF2 configuration and built-in common-password, similarity and numeric validators, with a 12-character minimum and 128-character input maximum. Never store/log plaintext passwords or implement cryptography. Exact hasher work factors track the selected patched Django release.

Local registration creates a customer only; role/staff flags are not writable input. No public registration or real password-reset delivery until verified email ownership, abuse protection and provider choices are implemented. Local development reset uses Django token generator and a local mail sink visible only to the developer; generic responses prevent account enumeration. Reset expiry default one hour, configurable. Development sink may hold reset tokens and must never feed shared application logs.

## Sessions and Origin

Database-backed Django sessions; cookie HttpOnly, SameSite=Lax and Secure for HTTPS deployments. No JWT or localStorage credentials. Same-origin frontend/API/admin in deployed design; local Vite proxy handles /api and /admin with /static proxy for Django admin assets. Do not enable permissive credentialed CORS.

Customer sessions expire after 12 hours; staff after one hour, configured at login, with no indefinite sliding extension. These are provisional policy defaults. Rotate session on login, flush on logout, invalidate on password reset/change using Django's supported mechanisms and tests. Inactive users cannot authenticate.

CSRF token bootstrap endpoint, CSRF header for unsafe requests, explicit CSRF enforcement on registration/login/password reset as well as authenticated mutations. DRF SessionAuthentication alone does not protect anonymous login views. Staff authorization and CSRF apply to admin/custom admin actions too.

## Authorization

| Actor | Allowed | Denied |
|---|---|---|
| Anonymous | Read active catalog; CSRF bootstrap; local auth initiation | Orders, inventory mutation, user enumeration |
| Active customer | Own checkout, order list/detail, own payable-order payment and cancellation | Other customers' orders; staff actions; setting price/status/owner |
| Staff with named permissions | Catalog management, audited stock adjustment, order inspection and explicit pending-order cancellation | Arbitrary state edits, silent stock overwrite, granting own privileges |
| Superuser | Bootstrap/break-glass only | Routine usage policy forbids treating it as normal staff |

Use Django groups and explicit permissions, not is_staff alone. Staff admin access does not automatically grant broad customer API queries. Cross-owner lookups return 404. All list/detail/action paths enforce ownership, including idempotency replay. Same-user UUID knowledge does not grant access.

## Administration

Django admin is the initial internal UI; React remains the customer UI. Read-only order/payment/reservation fields, no generic delete/bulk update for historical business data. Catalog writes and custom stock/cancellation actions call domain services and append sanitized audit entries. Fail/rollback an administrative mutation if required audit persistence fails.

## Secrets, Inputs and Exposure

Secrets/config via environment, ignored local env files and example placeholders only. Backend fails fast for missing required configuration. Never expose secrets through VITE_ variables. DEBUG disabled outside local tests; allowlisted hosts and trusted origins; parameterized ORM queries and plain-text descriptions (no arbitrary HTML).

Local DRF throttles are defense-in-depth only, not a distributed brute-force control. Before public exposure, choose and validate shared auth throttling, staff MFA/access restrictions, real mail/verification, TLS and security headers (including a CSP matching built assets). No claim that those controls already exist.

## Sources

[Django sessions](https://docs.djangoproject.com/en/5.2/topics/http/sessions/), [custom users](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/), [password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/), [CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/), [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/).
