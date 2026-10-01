# Decision Register and Deferred Gates

Updated: 2026-10-01. Decisions 0013–0021 were made by Codex under explicit user delegation for that round; ADR-0024 was selected under the owner's 2026-10-01 autonomous implementation delegation. That delegation applies to the active production-readiness goal; material technical choices will be recorded in ADRs and still require external resources for live verification. [ADR index](../decisions/README.md).

## Current Baseline — DECIDED

| Area | Selected direction | Record |
|---|---|---|
| Product | Registered checkout, one stock pool, simulated shipping/tax boundary | ADR-0013 |
| Workflow | Atomic reservation, one payment attempt, pending-only cancellation, expiry | ADR-0014 |
| Data | UUIDv4, EUR decimals, snapshots, explicit FKs/locks | ADR-0015 |
| Identity/admin | Django sessions, same origin/CSRF, custom user, restricted Django admin | ADR-0016 |
| API | JSON REST v1, Problem Details, drf-spectacular, scoped idempotency | ADR-0017 |
| Frontend | Router/Query, generated OpenAPI types (generator superseded by ADR-0022), temporary cart, shared stylesheet | ADR-0018, ADR-0022 |
| Tooling/local | Runtime lines, uv/npm, native apps + Compose PostgreSQL | ADR-0019 |
| Quality | Test pyramid, PostgreSQL concurrency, migration procedure, GitHub Flow policy | ADR-0020 |
| Operations | Logs/audit, health checks, maintenance; defer distribution | ADR-0021 |
| Authentication abuse controls | Atomic PostgreSQL fixed-window limits for customer/Admin login and local registration | ADR-0024 |

These choices supplement, not supersede, ADR-0001 through ADR-0012. Runtime completion is tracked in [project status](../project-status.md); accepted design alone is not evidence that a capability is implemented.

## Provisional Configurable Defaults — DECIDED for Local Simulation

15-minute reservation, 60-second maintenance cycle, 24-hour minimum idempotency retention, 12-hour customer session/one-hour staff session and password reset expiry, list size 20/max100, 50 distinct order lines/max99 units per line, 64 KiB API body limit. These are initial policy defaults, not measured capacity/security guarantees. Tests must inject clocks and settings.

## Implementation-Time Verification — HISTORICAL

| Item | Why not claim complete | Required before |
|---|---|---|
| Exact patched versions and locks | Verified for current dependencies at the local-development milestone | Re-evaluate on dependency changes |
| Type-check/formatter configuration and generated client types | Implemented and exercised locally | Relevant API/UI changes |
| Concurrency, permissions, schema and migration tests | Implemented for current local application baseline | Extend for public account/payment behavior |
| Concrete model field lengths and indexes beyond specified invariants | Resolved for current models | Re-evaluate with new production workflows |
| Local port/image digest/settings details | Local Compose setup is reproducible; no production artifact/deployment yet | Production packaging |

Routine implementation choices can follow the accepted conventions; substantive changes need recorded authority.

## Deferred Architectural Decisions

| Area | Status | Trigger / required input |
|---|---|---|
| Real payment/refunds, post-payment cancellation | DEFERRED | Explicit scope extension and provider requirements |
| Tax, invoices, shipping coverage/charges/fulfillment | DEFERRED | Market/jurisdiction and commercial requirements before real sales |
| Guest checkout, variants, multiple warehouses/currencies/sellers | DEFERRED | Validated scope change |
| Public SEO strategy / server rendering | DEFERRED | Search acquisition goals; current SPA limitations acknowledged |
| Production SMTP delivery, mailbox ownership and verified-account policy | ACTIVE | Implement generic SMTP configuration and enforce verified ownership; live deliverability needs a verified sending domain/provider account |
| Trusted proxy parsing, edge/shared abuse controls, monitoring and staff MFA/access policy | ACTIVE | Implement allow-listed proxy and cross-source controls; volumetric protection/MFA operations need hosted edge/identity controls |
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
| SLOs, RPO/RTO, backup retention and restore architecture | ACTIVE | Implement portable hosted backup and restore drill; numeric targets require actual business impact and hosted validation |
| Load thresholds and scaling/autoscaling | DEFERRED | Representative workload scenarios and measurement |

## Risk and Readiness Boundary

Local development is complete. Public accounts, real-money processing and hosted real-PII operation remain unavailable until the security, provider and operational gates are verified. Technical implementation progress does not itself approve a public launch.

No estimate of remaining decision count can be exact before requirements evolve. Deferred does not mean rejected or inevitable.
