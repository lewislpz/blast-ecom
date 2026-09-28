# ADR-0021: Operational Baseline and Deferred Infrastructure

## Status

Accepted

## Date

2026-09-28

## Context

The initial synchronous local monolith needs diagnosability without unneeded infrastructure.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Structured logs and bounded maintenance process | Enough to observe initial workflows | Limited aggregation and alerting until deployment |
| Full observability/broker/cache platform now | More operational capabilities | No measured workload or public operations to justify cost |

## Decision

Use structured JSON application logs with UTC time, level, component, operation and server-generated request_id. Separate minimal business audit records from diagnostic logs. Define liveness and database-readiness endpoints without sensitive detail. Record simulated notifications durably in the same order-transition transaction, then mark delivery through a restartable maintenance command.

A notification insert failure rolls back the transition; a later delivery failure never reverses a committed purchase. A unique transition/notification key prevents duplicates. The local maintenance loop handles expiry and simulated delivery only; no generic job platform. Defer Redis, RabbitMQ, Celery, integration events, external payment, distributed sagas, tracing stack, cloud, Kubernetes, Helm, GitOps and Terraform until specified triggers. Defer quantitative SLOs, budgets, RPO/RTO and real-sales tax/shipping requirements rather than inventing them.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: No monitoring service or tested backup exists. Persistent data must not be exposed to real use until recovery and operational controls are implemented and tested.

## Reversibility

Low for adding telemetry; higher when external delivery semantics require a broker or outbox dispatcher.

## Reconsideration Trigger

First hosted environment, real integrations, measured saturation or documented reliability requirements.

## Related Decisions and Specifications

- [observability](../operations/observability.md).
- [decision-register](../roadmap/decision-register.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
