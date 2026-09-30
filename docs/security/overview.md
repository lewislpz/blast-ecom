# Security Baseline

Status: Accepted security design with catalog/admin controls and initial customer session/CSRF/order API controls implemented and targeted-tested. Independent review and full-slice high-risk gates remain pending. [ADR-0016](../decisions/ADR-0016-identity-and-administration.md).

## Identity

Custom AbstractUser-based user from initial migration, username removed in favor of normalized email as login identifier. Normalize consistently (trim and lowercase under the selected product policy), validate syntax and enforce case-insensitive uniqueness in the database as well as application validation. Email case handling is a product convention, not a claim about all email providers.

Use Django's password hashing API/default supported PBKDF2 configuration and built-in common-password, similarity and numeric validators, with a 12-character minimum and 128-character input maximum. Never store/log plaintext passwords or implement cryptography. Exact hasher work factors track the selected patched Django release.

Registration creates a customer only and is runtime-gated to `DEBUG=true`; role/staff flags are not writable input. There is no password-reset endpoint or delivery flow. No public registration or password reset until verified email ownership, abuse protection and provider choices are implemented.

## Sessions and Origin

Database-backed Django sessions; cookie HttpOnly, SameSite=Lax and Secure for HTTPS deployments. No JWT or localStorage credentials. Same-origin frontend/API/admin in deployed design; local Vite proxy handles /api and /admin with /static proxy for Django admin assets. Do not enable permissive credentialed CORS.

Customer sessions expire after 12 hours; staff after one hour, configured at login, with no indefinite sliding extension. These are provisional policy defaults. Django rotates session on login and logout flushes it. Password reset/change invalidation is not implemented because those flows do not exist. Inactive users cannot authenticate.

CSRF token bootstrap endpoint, `X-CSRFToken` header for unsafe requests, and explicit CSRF enforcement on local registration/login as well as authenticated mutations/logout. DRF SessionAuthentication alone does not protect anonymous login views. The CSRF cookie is HttpOnly; clients obtain the request token from bootstrap JSON and refresh it after session rotation. Staff authorization and CSRF apply to admin/custom admin actions too.

## Authorization

| Actor | Allowed | Denied |
|---|---|---|
| Anonymous | Read active catalog; CSRF bootstrap; local auth initiation | Orders, inventory mutation, user enumeration |
| Active customer | Own checkout, order list/detail, own payable-order payment and cancellation | Other customers' orders; staff actions; setting price/status/owner |
| Staff with named permissions | Catalog management, audited stock adjustment, order inspection and explicit pending-order cancellation | Arbitrary state edits, silent stock overwrite, granting own privileges |
| Superuser | Bootstrap/break-glass only | Routine usage policy forbids treating it as normal staff |

Use Django groups and explicit permissions, not is_staff alone. The implemented catalog admin requires named model permissions; stock adjustment additionally requires `inventory.adjust_stock`. Superusers are deliberately excluded from routine catalog/inventory ModelAdmin operations. Order HTTP routes require an active non-staff customer and scope reads/mutations/replays to that owner. Same-user UUID knowledge does not grant access.

## Administration

Django admin is the initial internal UI; React remains the customer UI. Implemented catalog records can be managed only with explicit add/change/view permissions and cannot be deleted through admin. Stock counters are read-only in admin; stock changes use the transactional adjustment form and append actor, reason and delta. Order/payment/reservation fields and custom order actions remain planned. The stock counter and its adjustment audit record commit or roll back together.

## Secrets, Inputs and Exposure

Secrets/config via environment, ignored local env files and example placeholders only. Backend fails fast for missing required configuration. Never expose secrets through VITE_ variables. DEBUG disabled outside local tests; allowlisted hosts and trusted origins; parameterized ORM queries and plain-text descriptions (no arbitrary HTML).

No authentication throttling is currently configured. Before public exposure, choose and validate shared auth throttling, staff MFA/access restrictions, real mail/verification, TLS and security headers (including a CSP matching built assets). No claim that those controls already exist.

## Sources

[Django sessions](https://docs.djangoproject.com/en/5.2/topics/http/sessions/), [custom users](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/), [password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/), [CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/), [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/).
