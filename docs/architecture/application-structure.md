# Application Structure

Status: The repository and initial runtime skeleton are implemented. Only the custom Users model/migration and a non-functional React landing placeholder exist; the remaining domain modules and behavior below are planned. [ADR-0003](../decisions/ADR-0003-repository-strategy.md), [ADR-0015](../decisions/ADR-0015-data-model-conventions.md), [ADR-0018](../decisions/ADR-0018-frontend-conventions.md).

```text
backend/
  pyproject.toml
  uv.lock
  manage.py
  config/                 Settings and Django entry points
  modules/
    users/                Custom AbstractUser and initial migration (implemented)
    products/             Planned
    inventory/            Planned
    orders/               Planned
    payments/             Planned simulator module
    notifications/        Planned local durable intent
  common/                 Planned minimal request/error/idempotency infrastructure
  tests/                  Shared backend test support (planned)
frontend/
  package.json
  package-lock.json
  src/
    App.tsx                Current scaffold-only placeholder
    app/                  Planned routing/providers/application shell
    features/             Planned catalog, account, cart, checkout, orders
    shared/               Planned fetch adapter and generated API types
```

Each future Django module has an unambiguous app label and owns its writes. Models and constraints represent persistence; services expose commands; selectors expose reads; serializers validate/shape HTTP; views handle transport/auth and call domain operations. Admin actions use those same operations.

Orders will coordinate checkout/payment/cancellation in the application layer, calling Inventory and Payments operations rather than updating their tables directly. The coordinator owns the atomic transaction; module operations participate without committing independently. Cross-module reads use explicit selectors and accepted foreign keys only.

Do not add generic repositories, one class per operation, internal HTTP, event bus, broker or cache merely to mimic future microservices. Django framework tables are technical data; request/idempotency infrastructure is shared technical code rather than another business domain. The frontend depends on generated OpenAPI types, never ORM models.
