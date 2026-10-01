# Initial Use Cases

Status: UC-01 through UC-10 core local flows are implemented with PostgreSQL-backed tests and a verified browser journey. Notification processing is simulated locally; external delivery and account recovery remain deferred.

| ID | Actor | Intent | Acceptance |
|---|---|---|---|
| UC-01 | Visitor/customer | Browse catalog | Implemented: only active products/categories; deterministic pagination, category filter and title/price sort |
| UC-02 | Staff | Maintain catalog | Implemented: named admin permissions; products/categories archive instead of delete |
| UC-03 | Staff | Adjust stock | Implemented: permission-gated audited delta; row lock and invariant keep on_hand >= reserved |
| UC-04 | Customer | Place order | Implemented API and browser flow: current-price check, all-or-nothing reservation, snapshots and scoped idempotency |
| UC-05 | Customer | View history/detail | Implemented owner-scoped API, browser history and immutable snapshots |
| UC-06 | Customer/staff | Cancel eligible order | Customer API/domain/UI operation implemented: awaiting_payment before expiry only; release once; staff action remains pending |
| UC-07 | Customer | Resolve payment simulation | Implemented API and browser flow: one server-selected simulated outcome and atomic stock/order transition |
| UC-08 | Maintenance | Expire overdue orders | Implemented bounded local command: per-order transaction and locked-state recheck |
| UC-09 | Maintenance | Process simulated notification | Implemented: pending intent survives restart, then is marked locally simulated; no purchase reversal or external message |
| UC-10 | Visitor/customer | Register/login/logout/view account | Implemented: DEBUG-only local registration, generic login failures, PostgreSQL-backed attempt limits, CSRF bootstrap, bounded session and browser account flow; public account controls remain pending |
| UC-11 | Customer | Reset password | Deferred; endpoint, verified ownership and delivery are not implemented |

Detailed state/race behavior: [purchase workflow](purchase-workflow.md). HTTP contract: [API standards](../api/standards.md). Verification: [first slice](../development/first-slice.md).
