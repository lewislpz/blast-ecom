# Initial Data Model

Status: User, Category, Product, StockItem, StockAdjustment, Reservation, Order, OrderItem, PaymentAttempt, NotificationIntent, IdempotencyRecord and AuditEntry models/migrations are implemented and tested on PostgreSQL 17.11. Customer session/API integration and notification delivery/retention maintenance remain pending. [ADR-0015](../decisions/ADR-0015-data-model-conventions.md).

## Common Conventions

Domain records use UUIDv4 primary keys, UTC created_at and updated_at where mutable. Technical framework tables may use native Django IDs. EUR amounts use DecimalField(12,2), nonnegative except signed stock adjustments are quantities, not money. Product price must be positive. Amounts are JSON strings with exactly two decimal places; no binary float. With integer quantities and two-decimal prices, v1 requires no currency conversion or tax rounding algorithm. Validate calculated totals against field bounds before writes.

## Owned Records

| Module | Record | Principal fields and constraints |
|---|---|---|
| Users | User | Custom user from first migration; UUID, normalized email with DB uniqueness, password hash, active/staff flags and Django groups/permissions |
| Products | Category | UUID, unique slug, name, active flag; one category per product initially |
| Products | Product | UUID, unique SKU, category FK, title, plain-text description, EUR unit_price, active, optional bundled image key |
| Inventory | StockItem | One-to-one product FK, on_hand, reserved; integer checks on_hand >= 0, reserved >= 0, reserved <= on_hand |
| Inventory | Reservation | Order FK, product FK, positive quantity, state active/consumed/released; unique(order, product) |
| Inventory | StockAdjustment | Product FK, signed nonzero delta, actor FK, reason, UTC time; append-only |
| Orders | Order | Customer FK, state, EUR totals, expires_at, delivery snapshot, transition timestamps |
| Orders | OrderItem | Order FK, product FK, SKU/title/price snapshots, positive quantity, line_total; unique(order, product) |
| Payments | PaymentAttempt | One-to-one order FK, succeeded/failed, amount/currency snapshot, simulator reference, timestamp |
| Notifications | NotificationIntent | Order FK, transition code, pending/simulated state and timestamps; unique(order, transition code), state/created index |
| Technical | IdempotencyRecord | User FK, operation, key, request hash, status/body result, expiry; unique(user, operation, key) |
| Technical | AuditEntry | Actor reference, action code, target UUID, sanitized change metadata, timestamp; append-only by application policy |

A record is added only in its implementation slice; this table does not authorize a blanket scaffold. The listed core commerce records are now materialized by tasks 1–3.

Product creation through the owner operation initializes a zero-stock record in the same transaction. The public API reports only the derived `in_stock` boolean; it does not expose exact stock counts. Stock adjustments update `on_hand` under a row lock and append an actor/reason/delta record in the same transaction. Django Admin does not expose direct StockItem edits or deletion of adjustments. Product price, stock counter and `reserved <= on_hand` database constraints are in PostgreSQL migrations.

## Relationships and Historical Integrity

Allow named foreign keys: Product→Category; StockItem→Product; Reservation→Order/Product; Order→User; OrderItem→Order/Product; PaymentAttempt→Order; NotificationIntent→Order; StockAdjustment→Product/User; IdempotencyRecord→User. Use PROTECT for historical/domain references; transient idempotency rows cascade with their user, and audit actor deletion sets the actor reference to null. Historical business rows are not deletable through normal APIs/admin. Account deactivation and product/category archiving replace routine deletion. Privacy erasure/retention for real personal data needs a dedicated policy before public operation.

Avoid serializing nested ORM graphs. Snapshots remain immutable even when referenced products/addresses change. No blanket soft-delete library.

## Constraints and Indexes

Use FK/unique indexes and explicit indexes for (customer, created_at, id) order listing, (state, expires_at) expiry scanning and pending notification scanning. Add catalog indexes only for selected query paths after examination. Cross-table aggregate invariants (sum(active reservations)=reserved, totals=sum(lines)) are maintained by transactional services and tested; they are not falsely described as SQL CHECK constraints. State/currency/amount checks and idempotency result pairing are additionally enforced by database constraints.

## Lock and Write Protocol

PostgreSQL default READ COMMITTED plus explicit atomic blocks. Lock hierarchy: idempotency key row first when applicable; existing Order row next; Product rows in sorted UUID order when validating catalog; StockItem rows in sorted product UUID order. No operation locks Order after already holding stock locks. Creation has no existing Order row: lock products/stock, then insert the new order within that transaction. Catalog admin updates respect product locks; stock adjustments lock stock only, cannot lower on_hand below reserved and never acquire order locks.

Each transition locks the Order before its StockItems and rechecks status and a fresh database clock reading after acquiring locks. PostgreSQL transaction-start time is not sufficient after a lock wait: use clock_timestamp() for the deadline comparison. Check one terminal transition only. Failure releases reserved, success decreases both on_hand/reserved, and compensation is never repeated for terminal reservations. Do not use skip_locked for customer stock allocation; it would confuse contention with unavailability. The expiry scanner currently processes bounded candidates in separate transactions; skip_locked may be evaluated if concurrent maintenance needs it.

Deadlocks/lock timeouts roll back the full transaction and return a retryable server error with request_id. No network calls while locks are held. Repeated requests preserve idempotency keys.

## Availability

available = on_hand - reserved. Expired-but-not-released reservations remain counted conservatively until a transactional expiry operation releases them. Never compute availability by ignoring expired reservations while the counter still includes them.

Migration ordering follows FK dependencies (Orders before Inventory reservations, etc.) without changing module ownership. Initial user model must precede dependent auth migrations.

References: [Django transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/), [row locks](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [Python UUID](https://docs.python.org/3.13/library/uuid.html). Catalog, inventory and order workflow constraints/operations have PostgreSQL integration coverage, including lock contention, replay, terminal transitions and rollback. HTTP ownership/CSRF and browser flows remain unimplemented.

Deadline clock semantics: [PostgreSQL current date/time functions](https://www.postgresql.org/docs/17/functions-datetime.html).
