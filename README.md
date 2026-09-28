# Blast Ecom

Blast Ecom is a single-seller ecommerce platform for physical goods in EUR. The first release is a local, fictional purchase simulation—not a live store or production service.

## Current Status

**Phase 1 — Core Domain & Application Foundation, increment 1 in progress.** Django and React scaffolds, lockfiles, quality checks and the custom UUID user model's initial migration are present. There is no catalog, checkout, PostgreSQL Compose service or functional authentication yet. The migration has not been applied to PostgreSQL.

## Implemented

- Python 3.13 / Django 5.2 / Django REST Framework project skeleton with a custom UUID-keyed user model and normalized unique email.
- React 19 / TypeScript / Vite scaffold with a Spanish placeholder page.
- Locked backend and frontend dependencies, lint/type/test/build commands, and one small smoke test per application.

## Planned

Registered checkout, catalog and stock management, order reservations, simulated payment, own order history, local PostgreSQL Compose and restartable maintenance. Payments, taxes, shipping, and notifications remain simulated or explicitly unspecified. Real sales and public deployment are out of scope.

## Architecture and Stack

- Modular monolith in a monorepo with six logical domain areas; they are not six deployed services.
- Django ORM and migrations, DRF APIs, PostgreSQL, and React SPA.
- Database sessions and same-origin CSRF are selected for the eventual customer flow; they are not implemented yet.
- UUIDv4 domain IDs, exact EUR decimal values and immutable purchase snapshots are the accepted data conventions.

See [ADRs](docs/decisions/README.md), [architecture](docs/architecture/overview.md), [current project status](docs/project-status.md) and [resolved tool versions](docs/development/tooling.md).

## Local Checks

The [local development guide](docs/development/local-development.md) lists prerequisites and commands. PostgreSQL is not configured locally yet; the full Django workflow is therefore not runnable until the Compose increment is completed.

## Documentation

- [Product scope and purchase workflow](docs/product/overview.md)
- [Architecture and module boundaries](docs/architecture/overview.md)
- [API standards](docs/api/standards.md)
- [Testing and security](docs/development/testing-strategy.md), [security baseline](docs/security/overview.md), [threat model](docs/security/threat-model.md)
- [Roadmap](docs/roadmap/roadmap.md) and [deferred decisions/launch gates](docs/roadmap/decision-register.md)

Capabilities are labeled **Implemented**, **Planned**, **Proposed**, **Under discussion**, or **Deprecated**. Accepted design is not evidence of runtime behavior or production readiness.
