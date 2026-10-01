# Domain Glossary

| Term | Meaning |
|---|---|
| User | Custom Django identity with normalized unique email; active/staff flags |
| Customer | Authenticated user buying and consulting own orders |
| Staff administrator | Internal actor with explicitly granted permissions |
| Product | Simple physical item with SKU, title, category and EUR price |
| Category | Active grouping of products |
| Stock pool | One logical aggregate stock location, not an assertion about a real warehouse |
| StockItem | Product on_hand and reserved counters |
| Available stock | on_hand minus reserved |
| Reservation | Order allocation with active, consumed or released state |
| Order | Purchase record with awaiting_payment, confirmed, failed, cancelled or expired state |
| Confirmed | Simulated payment succeeded and stock consumed; not shipped |
| OrderItem | Immutable SKU/title/price/quantity snapshot |
| PaymentAttempt | Single simulated succeeded/failed outcome for an order |
| NotificationIntent | Durable local communication intent; pending or simulated |
| Authentication attempt bucket | Expiring fixed-window counter keyed by an HMAC digest, shared across app processes |
| Idempotency key | User/operation-scoped retry identifier, distinct from request_id |
| Request ID | Diagnostic identifier, not a deduplication or authorization token |
| Domain module | Logical responsibility within the Django monolith, not a microservice |
| Product variant | Deferred concept, outside initial simple-product scope |

Core commerce and authentication terms describe implemented local behavior; product variant remains deferred. Exact model conventions are in [data model](../architecture/data-model.md).
