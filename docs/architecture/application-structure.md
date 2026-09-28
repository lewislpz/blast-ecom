# Application Structure

Status: Accepted design; directories below are planned, not present. [ADR-0015](../decisions/ADR-0015-data-model-conventions.md).

```text
backend/
  pyproject.toml
  uv.lock
  config/                 Django settings, root URLs, runtime entry points
  modules/
    users/
    products/
    inventory/
    orders/
    payments/
    notifications/
  common/                 minimal request/error/idempotency infrastructure
  tests/
frontend/
  package.json
  package-lock.json
  src/
    app/                  routing, providers, application shell
    features/             catalog, account, cart, checkout, orders
    shared/               fetch adapter, generated API types, basic UI
```

Each Django app has an unambiguous label matching its domain and only files it needs. Models/constraints describe persistence; services expose business commands; selectors expose reads; serializers validate/shape HTTP data; views handle HTTP/auth and call services. Admin actions call those same services.

Orders coordinates checkout/payment/cancellation in the application layer, calling Inventory and Payments operations. It does not update their tables directly. Products exposes catalog snapshots; Users supplies identity references; Notifications owns delivery records. Avoid reverse service imports into Orders: supply order UUID/reference and required values to subordinate operations. The coordinator owns the transaction; module operations participate rather than committing independently.

Cross-module reads use explicit selectors. Accepted foreign keys are listed in data architecture. Do not add generic repositories, one class per operation, internal HTTP or an event bus merely to emulate future services.

Django framework tables are technical data. Idempotency/request infrastructure in common is shared technical code, not a seventh business domain. No frontend dependency on ORM models; generated OpenAPI types are the HTTP boundary.
