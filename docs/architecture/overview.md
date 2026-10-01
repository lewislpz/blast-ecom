# Architecture Overview

Status: Accepted modular-monolith design; local application runtime is implemented with Docker Compose.

Single-seller physical-goods EUR store, Django modular monolith, monorepo and six logical domains. React serves customers; Django admin serves permitted staff. One logical PostgreSQL database per environment with a shared application schema.

```mermaid
flowchart TB
    Browser["Customer browser: React / TypeScript / Vite build"]
    Staff["Staff browser: Django admin"]
    subgraph Django["Django application — one codebase"]
        API["DRF API: sessions + CSRF"]
        Admin["Restricted admin actions"]
        Services["Domain operations: Users / Products / Inventory / Orders / Payments / Notifications"]
        Maintenance["DEBUG-only maintenance command: expiry + local notification simulation"]
        API --> Services
        Admin --> Services
        Maintenance --> Services
    end
    Browser -->|"same-origin JSON API via Vite proxy"| API
    Staff --> Admin
Services -->|"Django ORM + atomic transactions"| DB["PostgreSQL: shared application schema"]
```

The current local deployment runs the frontend dev server, Django API, PostgreSQL and maintenance command as Compose services. Only the frontend port and PostgreSQL development port are published, both on host loopback. This is a local development topology, not a production deployment design.

Local notification intents are durable rows created with order transitions. The bounded DEBUG-only maintenance pass claims rows with PostgreSQL row locks, emits a console-only message and marks success as simulated; failed attempts remain pending for a later run. Console output is at-least-once in a process/commit crash window. This is not external notification delivery. See [ADR-0026](../decisions/ADR-0026-local-notification-processing.md).

This is a logical view, not a final deployment topology. Maintenance is a separate local process using the same codebase/domain operations, not a separately owned microservice. Same-origin proxy design does not select a cloud or reverse-proxy vendor. No broker/cache is required initially.

## Boundaries

| Module | Owns |
|---|---|
| Users | Identity/profile and account operations |
| Products | Catalog, category and current price |
| Inventory | Counters, reservations and adjustments |
| Orders | Purchase snapshots, lifecycle and coordination |
| Payments | Simulated payment outcome |
| Notifications | Durable intent and simulated delivery state |

Each module controls its writes. Orders coordinates via in-process operations; exact accepted FKs/lock order are in the [data model](data-model.md). Shared storage is not permission isolation.

## Key Invariants

No overselling, no duplicated transition effects, immutable purchase snapshots, owner-only order access and no post-commit purchase reversal on notification delivery failure. These are testable requirements, not runtime guarantees.

See [purchase workflow](../product/purchase-workflow.md), [application structure](application-structure.md), [data architecture](data-architecture.md), [security](../security/overview.md) and [API](../api/standards.md).

Real payment/shipping/tax rules, public account protections, hosting, availability, recovery and advanced observability remain launch gates in the [decision register](../roadmap/decision-register.md).
