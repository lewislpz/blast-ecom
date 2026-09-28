# Initial Threat Model

Status: Design review only. No controls have been implemented or penetration-tested.

Assets: customer identities/addresses, session secrets, order history, stock accuracy, administrative privileges and developer credentials.

Trust boundaries: browser→HTTP API; browser→admin; application→PostgreSQL; configuration→runtime; local mail sink→developer; generated API types→frontend. Browser payloads and administrative form input remain untrusted. Module ownership is a code boundary, not separate database credentials.

| Threat | Impact | Planned control | Required verification |
|---|---|---|---|
| Cross-customer object access | Address/order disclosure | Owner-scoped selectors on lists, detail, mutations and replay | Use another user's UUID/key for every route |
| Price/status/role tampering | Fraud or privilege escalation | Explicit input allowlist; server totals; staff fields read-only | Submit forged totals, roles and nested fields |
| CSRF including anonymous login | Unwanted actions or login confusion | Same-origin design and explicit Django CSRF checks | Missing/wrong token and foreign Origin tests on all unsafe auth routes |
| Session theft/fixation | Account compromise | HttpOnly/Secure/Lax, rotation, expiry, logout revocation | Reuse old session across login/logout/password reset |
| Password guessing/enumeration | Account takeover | Generic responses, validators, public shared throttling gate | Failure responses, abuse tests before exposure |
| Concurrent checkout/replay | Oversell or duplicate charge effects | Row locks, constraints, scoped idempotency | Real PostgreSQL concurrent last-unit/race tests |
| Admin bypasses domain logic | Inventory/order corruption | Restricted admin, service actions and transactional audit | Generic edit/delete/bulk paths cannot bypass actions |
| Stored description script | Browser compromise | Plain text, React escaping, no arbitrary HTML | Script-shaped strings render as text |
| Secret/PII in logs | Data leak | Allowlisted metadata; no bodies/cookies/passwords/addresses | Capture logs during errors and auth flows |
| Maintenance crash | Stock held too long, delayed notifications | Deadline checks, durable intents, restartable commands | Kill/restart scenarios and backlog visibility |
| Destructive migration | Lost history or stock | Expand/contract, review, backup/restore gates | Clean/upgrade tests; recovery test before real data |

Residual gates: email ownership, public auth abuse controls, staff MFA, real data retention/erasure, hosted TLS/secrets, backup restoration and external provider threats. Auth implementation must use the repository's high-risk review/test gates; this document does not satisfy future runtime gates automatically.
