# Initial Use Cases

Status: Accepted specifications; implementation is pending.

| ID | Actor | Intent | Acceptance |
|---|---|---|---|
| UC-01 | Visitor/customer | Browse catalog | Only active products/categories; deterministic paginated list |
| UC-02 | Staff | Maintain catalog | Permissions checked; archive referenced records |
| UC-03 | Staff | Adjust stock | Audited delta; on_hand never below reserved |
| UC-04 | Customer | Place order | Current-price check, all-or-nothing reservation and scoped idempotency |
| UC-05 | Customer | View history/detail | Only own records and immutable purchase snapshots |
| UC-06 | Customer/staff | Cancel eligible order | awaiting_payment before expiry only; release once |
| UC-07 | Customer | Resolve payment simulation | One outcome, atomic stock/order transition |
| UC-08 | Maintenance | Expire overdue orders | Recheck locked state; never release consumed stock |
| UC-09 | Maintenance | Deliver simulated notification | Pending intent survives crash; no purchase reversal |
| UC-10 | Visitor/customer | Account session/reset | CSRF, identity ownership and local reset delivery rules |

Detailed state/race behavior: [purchase workflow](purchase-workflow.md). HTTP contract: [API standards](../api/standards.md). Verification: [first slice](../development/first-slice.md).
