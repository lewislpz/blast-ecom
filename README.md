# Blast Ecom

Blast Ecom is a single-seller ecommerce platform for physical goods in EUR. The first release is a local, fictional purchase simulation—not a live store or production service.

## Current Status

**Phase 1 — Core Domain & Application Foundation.** Runtime scaffold, catalog/inventory, transactional order domain, session/CSRF APIs and customer browser journey are implemented and locally verified against PostgreSQL. Persistent PostgreSQL Compose setup and notification delivery remain pending. This is a local simulation, not production-ready commerce.

## Implemented

- Python 3.13 / Django 5.2 / Django REST Framework project skeleton with a custom UUID-keyed user model and normalized unique email.
- React 19 / TypeScript / Vite storefront with catalog, product detail, temporary cart, local-demo account flow, checkout, payment simulation, cancellation and own order history.
- Read-only public active catalog API, category filtering, deterministic product sorting, pagination and stock availability indicator.
- Staff-permission-gated Django Admin catalog management and append-only audited stock adjustments that respect reserved units.
- Atomic order creation with current-price checks, address/product snapshots, stock reservations, scoped idempotency, payment simulation, cancellation and expiry transitions. PostgreSQL tests cover contention and rollback.
- Durable append-only audit entries and transactional notification intents for order lifecycle transitions.
- RFC 9457 Problem Details for DRF errors; OpenAPI generation and validation for the catalog contract.
- Locked backend and frontend dependencies, generated OpenAPI TypeScript contracts, lint/type/test/build commands, PostgreSQL-backed backend tests, frontend behavior/API-client tests and browser E2E purchase coverage.
- Same-origin session authentication with CSRF bootstrap, login/logout/current-user; local registration is available only when `DEBUG=true`.
- Owner-scoped order list/create/detail/payment-simulation/cancel APIs, idempotency headers, strict request validation, 64 KiB request cap, Problem Details and generated OpenAPI.

## Planned

Local PostgreSQL Compose, notification-delivery simulation and restartable maintenance. Password reset, email verification, shared authentication abuse controls and staff MFA are not implemented; public account use is not ready. Payments, taxes, shipping, and notifications remain simulated or explicitly unspecified. Real sales and public deployment are out of scope.

## Architecture and Stack

- Modular monolith in a monorepo with six logical domain areas; they are not six deployed services.
- Django ORM and migrations, DRF APIs, `drf-spectacular` OpenAPI, PostgreSQL, and React SPA.
- Database sessions and same-origin CSRF are implemented for local API flows; public deployment controls remain incomplete.
- UUIDv4 domain IDs, exact EUR decimal values and immutable purchase snapshots are the accepted data conventions.

See [ADRs](docs/decisions/README.md), [architecture](docs/architecture/overview.md), [current project status](docs/project-status.md) and [resolved tool versions](docs/development/tooling.md).

## Local Checks

The [local development guide](docs/development/local-development.md) lists prerequisites and commands. PostgreSQL was validated with a temporary container; a persistent, reproducible Compose setup is still planned, so the documented full local workflow is not yet available.

## Documentation

- [Product scope and purchase workflow](docs/product/overview.md)
- [Architecture and module boundaries](docs/architecture/overview.md)
- [API standards](docs/api/standards.md)
- [Testing and security](docs/development/testing-strategy.md), [security baseline](docs/security/overview.md), [threat model](docs/security/threat-model.md)
- [Roadmap](docs/roadmap/roadmap.md) and [deferred decisions/launch gates](docs/roadmap/decision-register.md)

Capabilities are labeled **Implemented**, **Planned**, **Proposed**, **Under discussion**, or **Deprecated**. Accepted design is not evidence of runtime behavior or production readiness.
