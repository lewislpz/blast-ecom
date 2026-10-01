# Blast Ecom

Blast Ecom is a single-seller ecommerce platform for physical goods in EUR. The first release is a local, fictional purchase simulation—not a live store or production service.

## Current Status

**Phase 1 — Core Domain & Application Foundation.** Catalog/inventory, transactional orders, session/CSRF APIs, local account recovery/demo verification, customer browser journey, local console notifications and PostgreSQL backup/restore are implemented. Docker Compose now provides the local API, frontend, maintenance worker and PostgreSQL workflow. This is not production-ready commerce.

## Implemented

- Python 3.13 / Django 5.2 / Django REST Framework project skeleton with a custom UUID-keyed user model and normalized unique email.
- React 19 / TypeScript / Vite storefront with catalog, product detail, temporary cart, local-demo account flow, checkout, payment simulation, cancellation and own order history.
- Read-only public active catalog API, category filtering, deterministic product sorting, pagination and stock availability indicator.
- Staff-permission-gated Django Admin catalog management and append-only audited stock adjustments that respect reserved units.
- Atomic order creation with current-price checks, address/product snapshots, stock reservations, scoped idempotency, payment simulation, cancellation and expiry transitions. PostgreSQL tests cover contention and rollback.
- Durable append-only audit entries and transactional notification intents for order lifecycle transitions.
- RFC 9457 Problem Details for DRF errors; OpenAPI generation and validation for the catalog contract.
- Locked backend and frontend dependencies, generated OpenAPI TypeScript contracts, lint/type/test/build commands, PostgreSQL-backed backend tests, frontend behavior/API-client tests and browser E2E purchase coverage.
- Same-origin session authentication with CSRF bootstrap, login/logout/current-user; PostgreSQL-backed source and source+identity attempt limits protect customer and Django Admin login, while local registration is available only when `DEBUG=true` and separately limited.
- DEBUG-only local password recovery and demo email-verification flows use Django's console email backend; reset/verification links never appear in API responses, and demo verification does not claim mailbox ownership or block local sign-in.
- Owner-scoped order list/create/detail/payment-simulation/cancel APIs, idempotency headers, strict request validation, 64 KiB request cap, Problem Details and generated OpenAPI.
- Local Compose API, Vite frontend, PostgreSQL and maintenance worker; locked app dependencies, explicit Django migrations, idempotent fictional catalog seed, database readiness endpoint and restartable bounded expiry/notification processing.
- DEBUG-only local PostgreSQL custom-format backup and restore with restrictive file permissions, no-overwrite backup paths and fresh-database-only targets.

## Planned

Hosted deployment and real external notification delivery are not implemented. Public account use is not ready: local console email does not prove mailbox ownership, and application attempt limits do not replace trusted-proxy configuration, edge-level controls, staff MFA, or monitoring required before public exposure. Payments, taxes and shipping remain simulated or explicitly unspecified. Real sales and public deployment are out of scope.

## Architecture and Stack

- Modular monolith in a monorepo with six logical domain areas; they are not six deployed services.
- Django ORM and migrations, DRF APIs, `drf-spectacular` OpenAPI, PostgreSQL, and React SPA.
- Database sessions and same-origin CSRF are implemented for local API flows; public deployment controls remain incomplete.
- UUIDv4 domain IDs, exact EUR decimal values and immutable purchase snapshots are the accepted data conventions.

See [ADRs](docs/decisions/README.md), [architecture](docs/architecture/overview.md), [current project status](docs/project-status.md) and [resolved tool versions](docs/development/tooling.md).

## Local Checks

The [local development guide](docs/development/local-development.md) lists the Docker Compose startup, migration, seed, backup and restore commands.

## Documentation

- [Product scope and purchase workflow](docs/product/overview.md)
- [Architecture and module boundaries](docs/architecture/overview.md)
- [API standards](docs/api/standards.md)
- [Testing and security](docs/development/testing-strategy.md), [security baseline](docs/security/overview.md), [threat model](docs/security/threat-model.md)
- [Roadmap](docs/roadmap/roadmap.md) and [deferred decisions/launch gates](docs/roadmap/decision-register.md)

Capabilities are labeled **Implemented**, **Planned**, **Proposed**, **Under discussion**, or **Deprecated**. Accepted design is not evidence of runtime behavior or production readiness.
