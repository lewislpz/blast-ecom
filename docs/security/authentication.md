# Authentication Flows

Status: Local demo flows are implemented. An explicitly enabled public-account path is implemented and locally tested, but remains disabled by default. SMTP delivery has not been validated against an external provider, and no hosted worker or production readiness is claimed. See [ADR-0029](../decisions/ADR-0029-public-account-security-and-email-delivery.md).

## Registration and Sign-In

Customer registration is available in local demo mode (`DEBUG=true`) or when `BLAST_ECOM_PUBLIC_ACCOUNT_FLOWS_ENABLED=true` is explicitly set. Public mode must only be enabled with valid production configuration, including SMTP credentials and a non-local sender domain. Passwords use Django's configured similarity, common-password, numeric-password and minimum-length validators. The local flow sends a console message and allows unverified demo sign-in. The public flow returns a generic HTTP 202 response and creates a minimal verification-email outbox record in the same transaction; customers cannot sign in or create orders until verification. Existing local accounts are not automatically marked verified.

Login uses a database-backed Django session, explicit CSRF protection and generic invalid-credential errors. Login rotates the session; logout revokes it. Customer and admin authentication attempts use PostgreSQL-backed application-level limits. These safeguards are not a public abuse-control or volumetric DoS boundary.

## Local Password Recovery

`POST /api/v1/auth/password-reset/` is CSRF-protected and throttled in both enabled modes. It accepts an email address and always returns HTTP 202 with the same response for missing, inactive, staff, passwordless and eligible customer accounts. The local mode sends a reset link to the console. Public mode queues eligible delivery in PostgreSQL and returns a generic response. The endpoint never returns the account identifier or token.

The email link places a user UUID and Django password-reset token in the browser URL fragment. The frontend removes the fragment from the visible URL/history and submits the values only in a CSRF-protected POST body. The token uses Django's default password-reset token generator, expires after one hour, is invalidated by password-state changes and is consumed by a successful password change. New passwords use the same server-side validators as registration. Password change invalidates previously authenticated sessions. Tokens are generated at delivery time and are not stored in the outbox, returned in API responses or written to application logs.

## Local Email Verification

Registration creates a nullable `email_verified_at` value and outputs a signed, one-hour verification link. In DEBUG, the link is sent to the local console and a signed-in customer can request it again through `POST /api/v1/auth/email-verification/`. In public mode, a generic anonymous resend route accepts an email address and queues a message only for an eligible unverified customer. `POST /api/v1/auth/email-verification/confirm/` validates the signed link and atomically marks the account once. Invalid, expired and replayed links fail generically.

The local message and UI explicitly state that this operation only changes demo state. Public verification is based on possession of the link delivered to the configured email address; it is required for customer sign-in and checkout. An external SMTP transport, domain ownership, deliverability, bounce/complaint processing and recovery have not been tested here.

## Outbox Processing

Public registration, reset and verification-resend create durable intents in `users_account_email_outbox`. The bounded `process_account_email_outbox` management command claims one row at a time with PostgreSQL `skip_locked`, sends outside the claim transaction, retries with exponential backoff, and dead-letters after eight attempts. Claiming immediately before send avoids expiring leases for later rows during a slow batch. Delivery remains at-least-once: a crash after an SMTP server accepts the current message but before the database records success may result in a duplicate. The repository does not yet configure a production scheduler, worker supervisor, retention job, alert or DLQ operations procedure. Do not enable public flows until those operational controls and an external SMTP test exist.

## Local Configuration

Local development uses `django.core.mail.backends.console.EmailBackend` and `blast-ecom-local@localhost`. Outside DEBUG, account routes remain disabled unless explicitly enabled; production startup validates security settings, and enabling public flows additionally requires an SMTP backend and credentials. Never commit credentials. The checked-in Compose setup does not enable public account flows and does not supply real SMTP credentials.

## Launch Gates

Before enabling public accounts in a hosted environment, verify SMTP and sender-domain configuration, supervise and alert on outbox retries/dead letters, establish bounce/abuse handling, configure trusted proxies and edge/shared abuse controls, define privacy/retention/erasure, restrict staff access with MFA, and obtain independent security and operational review. Local tests do not establish deliverability or production readiness.
