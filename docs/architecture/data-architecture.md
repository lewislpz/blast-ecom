# Data Architecture

Status: Accepted data design implemented for the local modular monolith: PostgreSQL schema ownership, Django ORM/migrations and transactional order workflows are active. Hosted recovery and availability design remain deferred.

## Organization and Ownership

One logical PostgreSQL database per environment and one shared application schema ([ADR-0010](../decisions/ADR-0010-data-organization.md)). Each business table has one owning module; other modules call internal operations to request writes ([ADR-0011](../decisions/ADR-0011-module-data-ownership.md)).

Use Django ORM and Django migrations ([ADR-0012](../decisions/ADR-0012-persistence-tooling.md)). UUIDv4, exact EUR decimals, snapshots, allowed FKs and lock order are now specified in the [initial model](data-model.md). SQL schema/database names and physical infrastructure remain implementation/deployment details.

## Consistency

Checkout/reservation and each payment/cancel/expiry transition are local atomic transactions. Row locks and constraints protect counters; idempotency records commit with effects. The application coordinator controls transaction boundaries, while owning modules perform writes.

Notification intent is recorded atomically, delivery happens later. Stock correctness and notification delivery have different timing guarantees. A scheduler outage can delay release conservatively; a payment command still checks expiry under lock.

## Evolution and Recovery

Review migrations, test clean/upgrade paths, prefer expand/contract and forward repairs; see [migration policy](../development/migrations.md). Shared FKs and recovery scope are deliberate initial tradeoffs, not technical debt by themselves. Service extraction would require explicit data/contract migration.

PostgreSQL integration and migration-drift checks exist. Automated backup/restore testing does not. Before hosted real data: concrete roles, secrets, backup/restore, retention and availability objectives must be designed and verified.
