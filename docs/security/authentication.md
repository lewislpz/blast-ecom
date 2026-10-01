# Authentication Flows

Status: Implemented for local development only. These flows do not establish public-account readiness or ownership of a real email mailbox.

## Registration and Sign-In

Customer registration is available only with `DEBUG=true`. It validates passwords using Django's configured similarity, common-password, numeric-password and minimum-length validators. New accounts receive a local verification message through Django's console email backend. Customers may still sign in before using that link; the verification flag is informational in this demo. Existing local accounts remain usable and are not automatically marked verified.

Login uses a database-backed Django session, explicit CSRF protection and generic invalid-credential errors. Login rotates the session; logout revokes it. Customer and admin authentication attempts use PostgreSQL-backed application-level limits. These safeguards are not a public abuse-control or volumetric DoS boundary.

## Local Password Recovery

`POST /api/v1/auth/password-reset/` is CSRF-protected, throttled and available only in DEBUG mode. It accepts an email address and always returns HTTP 202 with the same message for missing, inactive, staff, passwordless and eligible customer accounts. Eligible customers receive a reset link in the local Django console. The endpoint never returns the account identifier or token.

The local console email intentionally contains a manual-use link. It places a user UUID and Django password-reset token in the browser URL fragment. The frontend removes the fragment from the visible URL/history and submits the values only in a CSRF-protected POST body. The token uses Django's default password-reset token generator, expires after one hour, is invalidated by password-state changes and is consumed by a successful password change. New passwords use the same server-side validators as registration. Password change invalidates previously authenticated sessions. Tokens are not returned in API responses or written to application logs.

## Local Email Verification

Registration creates a nullable `email_verified_at` value and outputs a signed, one-hour local verification link in the Django console. A customer can request the link again while signed in through `POST /api/v1/auth/email-verification/`. `POST /api/v1/auth/email-verification/confirm/` validates the signed link and atomically marks the account once. Invalid, expired and replayed links fail generically.

The message and UI explicitly state that this operation only changes demo state. A developer's ability to read the console is not evidence that the customer controls a real external mailbox. Verification is not required for local sign-in and must not be reused as a production identity control.

## Local Configuration

The backend uses `django.core.mail.backends.console.EmailBackend` and `blast-ecom-local@localhost`; no external SMTP/API provider or email credentials are configured. Reset and verification routes return not-found outside DEBUG. Keep the backend bound to local development and do not use real customer accounts or personal data.

## Launch Gates

Before any public account flow, replace the console backend with a reviewed delivery provider; establish domain/DNS/TLS and bounce/abuse handling; verify actual mailbox control; review enumeration and timing risks; configure trusted proxy and edge/shared abuse controls; define privacy, retention and erasure; and obtain an independent security review. Local flows are not evidence that these controls exist.
