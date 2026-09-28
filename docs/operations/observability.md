# Initial Observability Design

Status: Accepted design, not installed instrumentation. [ADR-0021](../decisions/ADR-0021-operations-baseline-and-deferrals.md).

## Questions and Evidence

| Question | Planned initial evidence |
|---|---|
| Is the process/database reachable? | Separate liveness and DB-readiness endpoints |
| Why did checkout fail? | request_id, operation, safe error code and duration |
| Are reservations stuck? | Maintenance summary: due/pending count, oldest overdue age, release failures |
| Did payment simulation alter stock once? | Transition/audit records and invariant tests |
| Are simulated notifications pending? | Pending count, attempts and last successful maintenance pass |

JSON logs: UTC timestamp, level, component, environment, request_id, operation, duration_ms, safe code. Server generates bounded request IDs; do not blindly trust incoming headers. No request/response bodies, email, address, password, reset token, session cookie or DB connection string in logs.

Business audit is separate: actor, operation, target UUID, timestamp, reason and bounded non-sensitive changes for staff mutations/order transitions. No claim of tamper-proof audit or regulatory retention.

Measure request durations/errors and workflow counts through initial logs/audit summaries; introduce a metrics backend only when operated workloads justify collection. Future metric labels exclude user/order/request IDs to avoid high cardinality.

No Prometheus, Grafana, Loki, tracing or alerts are deployed. First hosted environment requires concrete telemetry collection, actionable alert ownership and recovery procedures; numeric SLOs await user/workload requirements.
