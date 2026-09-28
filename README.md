# Blast Ecom

Blast Ecom is a single-seller ecommerce platform for physical goods in EUR, designed around a complete customer purchase and administration journey.

## Current Status

**Phase 0 — Product Definition & Architecture.** Twenty-one Accepted ADRs and an initial implementation specification exist. No application, database, automated application tests or deployment is implemented. The directory is not initialized as a Git repository.

## Accepted Architecture and Stack

- Modular monolith, monorepo, six logical areas: Users, Products, Inventory, Orders, Payments and Notifications.
- Python + Django + Django REST framework; Django ORM and Django migrations.
- React + TypeScript + Vite for customers; Django admin for internal staff.
- PostgreSQL: one logical database per environment, shared application schema, module-controlled writes.
- Registered checkout, Django database sessions, same-origin API and CSRF.
- UUIDv4 domain IDs, exact EUR decimals and immutable purchase snapshots.

See [ADRs](docs/decisions/README.md), [architecture](docs/architecture/overview.md) and [runtime/tool choices](docs/development/tooling.md). Exact locked versions are not yet resolved.

## Planned First Capabilities

Browse catalog, create a stock-reserved order, simulate payment, cancel before payment or expire, and view own order history. Staff manage catalog and stock through restricted actions. Payments, shipping and notifications are simulated; real tax/logistics policies remain launch gates.

The [purchase workflow](docs/product/purchase-workflow.md) and [first slice](docs/development/first-slice.md) define success and failure behavior. Confirmed does not mean shipped.

## Repository and Local Development

Current files: docs/, AGENTS.md, .codex/ and .orchestrator/. Future backend/ and frontend/ layout is documented but not created.

The [local development design](docs/development/local-development.md) uses native app processes and Compose PostgreSQL. No application execution/test commands, Dockerfiles, Compose or CI configuration exist yet.

## Quality, Security and Operations

[Testing](docs/development/testing-strategy.md), [security baseline](docs/security/overview.md), [threat model](docs/security/threat-model.md), [migration policy](docs/development/migrations.md) and [observability design](docs/operations/observability.md) are planned controls, not runtime guarantees.

## Navigation

- [Documentation index](docs/README.md)
- [Project status](docs/project-status.md)
- [Decision report](docs/reports/2026-09-28-phase0-decisions.md)
- [Deferred decisions and launch gates](docs/roadmap/decision-register.md)
- [Roadmap](docs/roadmap/roadmap.md)
# blast-ecom
# blast-ecom
