# Initial Use Cases

Status: UC-01 browse, UC-02 catalog maintenance, UC-03 stock adjustment, core UC-04/06/07/08 domain operations, customer session endpoints and owner-scoped order APIs are implemented with PostgreSQL-backed tests. Browser flow and notification delivery remain pending.

| ID | Actor | Intent | Acceptance |
|---|---|---|---|
| UC-01 | Visitor/customer | Browse catalog | Implemented: only active products/categories; deterministic pagination, category filter and title/price sort |
| UC-02 | Staff | Maintain catalog | Implemented: named admin permissions; products/categories archive instead of delete |
| UC-03 | Staff | Adjust stock | Implemented: permission-gated audited delta; row lock and invariant keep on_hand >= reserved |
| UC-04 | Customer | Place order | Implemented API: current-price check, all-or-nothing reservation, snapshots and scoped idempotency; browser pending |
| UC-05 | Customer | View history/detail | Implemented owner-scoped API and immutable snapshots; browser pending |
| UC-06 | Customer/staff | Cancel eligible order | Customer API/domain operation implemented: awaiting_payment before expiry only; release once; staff action pending |
| UC-07 | Customer | Resolve payment simulation | Implemented API: one server-selected simulated outcome and atomic stock/order transition; browser pending |
| UC-08 | Maintenance | Expire overdue orders | Domain operation implemented: per-order transaction and locked-state recheck; periodic command pending |
| UC-09 | Maintenance | Deliver simulated notification | Pending intent survives crash; no purchase reversal |
| UC-10 | Visitor/customer | Register/login/logout/view account | Implemented: DEBUG-only local customer registration, generic login failures, CSRF bootstrap, bounded session and logout; public account controls and browser pending |
| UC-11 | Customer | Reset password | Deferred; endpoint, verified ownership and delivery are not implemented |

Detailed state/race behavior: [purchase workflow](purchase-workflow.md). HTTP contract: [API standards](../api/standards.md). Verification: [first slice](../development/first-slice.md).
