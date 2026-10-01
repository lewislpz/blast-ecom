# Initial Threat Model

Status: Local development security baseline implemented. Targeted tests cover auth/session lifecycle, request validation, owner isolation, schema, secret-safe logging and Group-admin privilege boundaries. Group administration is break-glass-only per [ADR-0023](../decisions/ADR-0023-break-glass-group-administration.md). This is not a production threat assessment.

Assets: customer identities/addresses, session secrets, order history, stock accuracy, administrative privileges and developer credentials.

Trust boundaries: browser→HTTP API; browser→admin; application→PostgreSQL; configuration→runtime; local mail sink→developer; generated API types→frontend. Browser payloads and administrative form input remain untrusted. Module ownership is a code boundary, not separate database credentials.

| Threat | Impact | Current control | Verification and residual risk |
|---|---|---|---|
| Cross-customer object access | Address/order disclosure | Owner-scoped selectors on lists, detail, mutations and replay | PostgreSQL API test confirms another user's UUID cannot list/read/act on order |
| Price/status/role tampering | Fraud or privilege escalation | Explicit input allowlist; server totals; staff fields read-only | Submit forged totals, roles and nested fields |
| CSRF including anonymous login | Unwanted actions or login confusion | Explicit Django CSRF checks on unsafe auth/order routes; JSON token bootstrap | Missing/invalid token and untrusted Origin tested across customer registration, login, logout, order creation, payment and cancellation; trusted local Vite Origin has a positive test |
| Session theft/fixation | Account compromise | HttpOnly/Secure/Lax, login rotation, bounded expiry, logout revocation | Session rotation, expiry and logout tested; password reset does not exist |
| Password guessing/enumeration | Account takeover | Generic login failures and atomic PostgreSQL source plus source+identity limits for customer/Admin login; local registration has a separate policy | PostgreSQL threshold, normalization, source isolation, concurrency, generic 429, HMAC storage, CSRF ordering and fail-closed behavior tested; distributed attacks remain possible |
| Concurrent checkout/replay | Oversell or duplicate charge effects | Row locks, constraints, scoped idempotency | PostgreSQL domain races/replay and API owner isolation/replay tests pass |
| Admin bypasses domain logic or group privilege escalation | Inventory/order corruption or unauthorized staff privilege | Catalog operations use owner services; stock counters are read-only and adjustment writes are permission-gated, locked and audited; Group admin is restricted to active staff superusers | PostgreSQL tests verify ordinary staff cannot grant their group `inventory.adjust_stock`, while the break-glass superuser can; broader order admin paths remain unimplemented |
| Stored description script | Browser compromise | Plain text, React escaping, no arbitrary HTML | Script-shaped strings render as text |
| Secret/PII in logs | Data leak | Allowlisted metadata; no bodies/cookies/passwords/addresses | Capture logs during errors and auth flows |
| Maintenance crash | Stock held too long, delayed notifications | Deadline checks, durable intents, restartable commands | Kill/restart scenarios and backlog visibility |
| Destructive migration | Lost history or stock | Expand/contract, review, backup/restore gates | Clean/upgrade tests; recovery test before real data |

Residual limitations and launch gates: current authentication limits are app-level controls, use `REMOTE_ADDR`, and can be bypassed by distributed sources; they are not volumetric DoS protection. Login remains confined to trusted local development until trusted proxy parsing, an edge/shared abuse-control strategy and monitoring are deployed. Production reverse-proxy/scheme configuration, email ownership, staff MFA, real data retention/erasure, hosted TLS/secrets, backup restoration and external provider threats have not been implemented or assessed. This document is a local-development threat model, not production approval.
