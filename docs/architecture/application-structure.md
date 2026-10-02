# Application Structure

Status: Runtime, Users session API, catalog API/models, single-pool inventory, owner-scoped order API and order/reservation/payment-simulation domain operations, idempotency, audit records, durable notification intents and local React purchase journey are implemented. Notification delivery and hosted platform remain planned. [ADR-0003](../decisions/ADR-0003-repository-strategy.md), [ADR-0015](../decisions/ADR-0015-data-model-conventions.md), [ADR-0018](../decisions/ADR-0018-frontend-conventions.md), [ADR-0022](../decisions/ADR-0022-api-type-generator.md).

```text
backend/
  pyproject.toml
  uv.lock
  manage.py
  config/                 Settings and Django entry points
  modules/
    users/                Custom AbstractUser and initial migration (implemented)
    products/             Category/Product records, owner operations, public read API, staff catalog admin (implemented)
    inventory/            StockItem, Reservation, adjustments and owner operations (implemented)
    orders/               Order snapshots, state transitions, checkout/cancel/expiry operations (implemented)
    payments/             Local DEBUG simulator plus Stripe sandbox adapter/webhook (implemented; no live processing)
    notifications/        Durable transition intent records and local simulated processing (implemented; external delivery deferred)
  common/                 Problem Details, audit trail and scoped idempotency infrastructure (implemented)
  tests/                  Shared backend test support (planned)
frontend/
  package.json
  package-lock.json
  src/
    App.tsx                Query provider and route composition
    pages/                Catalog, product, cart, account, checkout, order pages
    shared/api/            Same-origin CSRF/session adapter and generated OpenAPI types
    shared/cart/           In-memory product-ID/quantity context
    styles/                Shared CSS tokens and responsive app stylesheet
    e2e/                   Local Playwright purchase and accessibility checks
```

Each Django module has an unambiguous app label and owns its writes. Models and constraints represent persistence; services expose commands; selectors expose reads; serializers validate/shape HTTP; views handle transport/auth and call domain operations. Implemented admin writes go through product/category operations and the transactional stock adjustment operation.

Orders coordinates checkout/payment/cancellation in the application layer, calling Inventory and Payments operations rather than updating their tables directly. The coordinator owns the atomic transaction; module operations participate without committing independently. Notifications and Common likewise expose owner operations for intent/audit writes. Cross-module reads use explicit selectors and accepted foreign keys only.

Do not add generic repositories, one class per operation, internal HTTP, event bus, broker or cache merely to mimic future microservices. Django framework tables are technical data; request/idempotency infrastructure is shared technical code rather than another business domain. The frontend depends on generated OpenAPI types, never ORM models.
