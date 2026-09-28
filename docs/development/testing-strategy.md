# Testing Strategy

Status: Accepted verification plan; no application tests have run. [ADR-0020](../decisions/ADR-0020-quality-and-migration-policy.md).

| Level | Tool/environment | Behavior |
|---|---|---|
| Unit | pytest, deterministic clock/simulator | Totals, input policies, transition eligibility |
| Integration | pytest-django + PostgreSQL | Constraints, rollback, row locks, ORM queries, migration history |
| API/contract | DRF test client + generated schema | Routes, errors, ownership, CSRF, idempotency and schema shape |
| Component | Vitest + React Testing Library | Loading/empty/error states, forms, cart and conflict recovery |
| E2E | Playwright + real local app/DB | Purchase success, failure/cancel and own-order visibility |
| Load | Deferred scenario-driven tooling | No invented performance thresholds |

Use transaction-enabled tests/separate DB connections for races. Do not substitute SQLite for stock locking tests. Avoid mocks of the ORM or transaction boundary; mock only external delivery (none initially) and deterministic time/result inputs.

Mandatory cases: last unit concurrent checkout; cancellation/payment race; expiry while waiting for lock; repeated same key and changed payload; new-key repeated payment; maintenance restart; stock adjustment below reserved; price change vs snapshot; notification insert rollback vs delivery failure; cross-owner list/detail/action/replay; anonymous login CSRF; staff action bypass; logs free of secrets/addresses.

Verify schema generated from serializers/views matches actual success/error bodies, security requirements and decimal representation. Changing schema regenerates frontend types. No E2E test compensates for missing ownership/concurrency tests.

Definition of Done for a slice: behavior implemented, relevant checks pass, migrations reviewed, docs/ADRs current, secrets/config reviewed, observable failures considered and remaining risks explicit. Auth implementation requires threat-model, tests, integration, independent review and user approval gates per repository rules.
