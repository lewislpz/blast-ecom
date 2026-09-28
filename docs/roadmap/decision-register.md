# Decision Register and Deferred Gates

Updated: 2026-09-28. Decisions 0013–0021 were made by Codex under explicit user delegation for this round, not individually approved by the user. [ADR index](../decisions/README.md).

## Current Baseline — DECIDED

| Area | Selected direction | Record |
|---|---|---|
| Product | Registered checkout, one stock pool, simulated shipping/tax boundary | ADR-0013 |
| Workflow | Atomic reservation, one payment attempt, pending-only cancellation, expiry | ADR-0014 |
| Data | UUIDv4, EUR decimals, snapshots, explicit FKs/locks | ADR-0015 |
| Identity/admin | Django sessions, same origin/CSRF, custom user, restricted Django admin | ADR-0016 |
| API | JSON REST v1, Problem Details, drf-spectacular, scoped idempotency | ADR-0017 |
| Frontend | Router/Query, generated types, temporary cart, CSS Modules | ADR-0018 |
| Tooling/local | Runtime lines, uv/npm, native apps + Compose PostgreSQL | ADR-0019 |
| Quality | Test pyramid, PostgreSQL concurrency, migration procedure, GitHub Flow policy | ADR-0020 |
| Operations | Logs/audit, health checks, maintenance; defer distribution | ADR-0021 |

These choices supplement, not supersede, ADR-0001 through ADR-0012. No app capability is Implemented.

## Provisional Configurable Defaults — DECIDED for Local Simulation

15-minute reservation, 60-second maintenance cycle, 24-hour minimum idempotency retention, 12-hour customer session/one-hour staff session and password reset expiry, list size 20/max100, 50 distinct order lines/max99 units per line, 64 KiB API body limit. These are initial policy defaults, not measured capacity/security guarantees. Tests must inject clocks and settings.

## Implementation-Time Verification — PENDING

| Item | Why not claim complete | Required before |
|---|---|---|
| Exact patched versions and locks | No resolver/build has run | Scaffold acceptance |
| Type-check/formatter configuration and generated client types | No source exists | Relevant slice completion |
| Concurrency, permissions, schema and migration tests | Specifications are not execution evidence | Application acceptance |
| Concrete model field lengths and indexes beyond specified invariants | Resolve with serializers/query paths | Associated model migration |
| Local port/image digest/settings details | Need reproducible executable setup | Local platform handoff |

Routine implementation choices can follow the accepted conventions; substantive changes need recorded authority.

## Deferred Architectural Decisions

| Area | Status | Trigger / required input |
|---|---|---|
| Real payment/refunds, post-payment cancellation | DEFERRED | Explicit scope extension and provider requirements |
| Tax, invoices, shipping coverage/charges/fulfillment | DEFERRED | Market/jurisdiction and commercial requirements before real sales |
| Guest checkout, variants, multiple warehouses/currencies/sellers | DEFERRED | Validated scope change |
| Public SEO strategy / server rendering | DEFERRED | Search acquisition goals; current SPA limitations acknowledged |
| Email verification/reset delivery provider | DEFERRED | Before public account use |
| Public shared auth throttling, staff MFA/access policy | DEFERRED | Before internet exposure |
| Privacy retention/erasure and audit retention | DEFERRED | Before real personal data |
| Redis/cache | DEFERRED | Measured latency/hot paths or an explicit shared-state requirement |
| RabbitMQ/Celery/integration events | DEFERRED | Durable external work or measured separation needs |
| Saga/outbox/inbox for external systems | DEFERRED | Cross-system atomicity/delivery problem; local notification intent is not a generic bus |
| App images/registry/release tags | DEFERRED | Working tested app and packaging milestone |
| CI provider/config and protected-branch checks | DEFERRED | Local checks and Git repository exist |
| Hosted development/staging/production | DEFERRED | Release audience, access and budget known |
| Cloud, Kubernetes, Helm, GitOps, Terraform | DEFERRED | Deployment/platform need and cost comparison |
| Production secrets/TLS/DNS/networking/storage | DEFERRED | Hosted topology selected |
| Metrics/log platform, tracing, alert ownership | DEFERRED | First operated environment and diagnostic needs |
| SLOs, RPO/RTO, backup retention and restore architecture | DEFERRED | Business impact and operated data; before real persistent use |
| Load thresholds and scaling/autoscaling | DEFERRED | Representative workload scenarios and measurement |

## Risk and Readiness Boundary

The next deliverable can be a local simulated implementation. No public/real-money/real-PII launch is approved. Known deployment requirements are not waived by marking local design decisions Accepted.

No estimate of remaining decision count can be exact before requirements evolve. Deferred does not mean rejected or inevitable.
