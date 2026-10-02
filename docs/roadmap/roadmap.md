# Roadmap

Status: The local first slice and Compose platform are complete; Phase 3 — Testing & Quality / pre-production hardening — is current. No public or hosted production operation is claimed. See the [decision report](../reports/2026-09-28-phase0-decisions.md) and [first slice](../development/first-slice.md).

| Phase | Intended outcome | Entry condition |
|---|---|---|
| 0 — Product Definition & Architecture | Initial local scope, domain rules, security and tool baseline documented | Complete; 29 Accepted ADRs and one Superseded ADR |
| 1 — Core Domain & Application Foundation | Tested local commerce journey and core abuse controls | Complete for the documented local first slice; see project status and ADRs |
| 2 — Local Platform | Reproducible local execution | Complete for local Compose API, frontend, PostgreSQL and maintenance workflow |
| 3 — Testing & Quality | Behavior, contract and browser verification | Current: security review and automated test fixtures pass; external Stripe sandbox validation is pending |
| 4 — Continuous Integration | Automated agreed checks | Pending: implement PR checks before provider-backed production release |
| 5 — Registry & Release Management | Versioned, reproducible artifacts | Packaging and release strategy selected |
| 6 — Deployment Platform Evaluation | Suitable deployment and rollback | Application, production artifacts and CI work; no provider account/budget yet |
| 7 — Continuous Delivery | Controlled promotion | Environment and deployment model selected |
| 8 — Infrastructure as Code | Reproducible infrastructure | Hosting, state and ownership selected; no cloud resources provisioned |
| 9 — Observability | Answer operational questions | Workloads and failure modes understood; no hosted telemetry deployed |
| 10 — Security Hardening | Validate and strengthen relevant controls | Public account controls and Stripe sandbox boundary implemented; hosted/runtime review remains required |
| 11 — Reliability & Operations | Tested recovery and actionable procedures | Hosted persistent data exists; backup/restore code and drills precede service-level claims |
| 12 — Scaling & Performance | Evidence-driven capacity improvements | Workload scenarios and measurements |
| 13 — Production Readiness | Explicit readiness review | Security, recovery, deployment and operation verified |

Kubernetes, Helm, GitOps and Terraform are candidates for later evaluation, not mandatory destinations. Testing, security and observability begin with relevant increments; their dedicated phases deepen existing work.

Accepted v1 scope is defined in [scope](../product/scope.md). Scope completion and production readiness are separate milestones. No deadlines or capacity targets are assumed.

Security/testing/observability are part of every relevant implementation increment. Later dedicated phases do not postpone essential controls. [Deferred gates](decision-register.md) distinguish missing commercial input from decisions that need runtime evidence.
