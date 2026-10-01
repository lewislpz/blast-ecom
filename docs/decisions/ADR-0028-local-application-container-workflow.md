# ADR-0028: Local Application Container Workflow

## Status

Accepted

## Date

2026-10-01

## Context

The application already has PostgreSQL-only Compose support. A reproducible development workflow should let a developer run the customer journey and maintenance processing without requiring Python and Node.js on the host, while retaining quick local iteration and explicit database setup.

## Decision Drivers

- Local startup should use one container platform and pinned project dependencies.
- Database migrations and fictional seed data must remain explicit actions.
- Local-only services and published ports must not imply a production topology.
- Application processes should run as non-root and contain no baked credentials.
- Source changes should be usable without rebuilding dependency layers.

## Options Considered

### Option A — Docker Compose development services

Run API, Vite, PostgreSQL and the maintenance worker in Compose. Bind-mount application source read-only for development; keep database storage in a named volume; publish only Vite and PostgreSQL on loopback. Run migration and seed commands explicitly.

Advantages:

- Consistent local runtime without host language runtimes.
- Existing database volume persists across normal container restarts.
- Service discovery allows realistic local API/frontend/worker interaction.

Disadvantages:

- Docker is required and consumes additional local resources.
- Development containers and Vite are not optimized or hardened for production deployment.

### Option B — Host processes with PostgreSQL in Compose

Run Django, Vite and maintenance directly on the developer's machine.

Advantages:

- Fast iteration and simple local debugger integration.
- Fewer running containers and lower runtime overhead.

Disadvantages:

- Requires compatible host Python/Node tooling and environment setup.
- Host-specific version drift makes the application path less reproducible.

## Decision

Use Option A as the standard local development path while keeping host-based checks available. Compose uses Python 3.13.15, Node 24.21.0 and PostgreSQL 17.11 images, locked dependencies, non-root app users, read-only source mounts, loopback-only published ports, explicit migration/seed commands and a named persistent database volume. No production deployment model is selected.

## Consequences

### Positive

- Developers can exercise API, browser, database and maintenance behavior with `docker compose`.
- Rebuilding images does not reset persisted PostgreSQL state.
- Migrations/seeding remain observable and opt-in.

### Negative

- Developers must understand container logs and Compose networking.
- PostgreSQL backup tools for the Django host commands remain an explicit local prerequisite.

### Risks

- Users can mistake a development image for a production image; documentation and Docker targets label them development-only.
- The named volume persists data after ordinary shutdown; destructive volume removal is not part of startup instructions.

## Related Decisions

- [ADR-0019: Tooling and Local Development](ADR-0019-tooling-and-local-development.md)
- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)
- [ADR-0027: Safe Local PostgreSQL Backup and Restore](ADR-0027-local-postgresql-backup-and-restore.md)

## Notes

Revisit only when hosted deployment, production artifacts, or non-Compose local requirements become an approved scope.
