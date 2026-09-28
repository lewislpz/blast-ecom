# Roadmap

Status: Proposed sequencing with an accepted local first-slice baseline. Phase 0 is current; no application implementation is authorized by this document. See the [decision report](../reports/2026-09-28-phase0-decisions.md) and [first slice](../development/first-slice.md).

| Phase | Intended outcome | Entry condition |
|---|---|---|
| 0 — Product Definition & Architecture | Initial local scope, domain rules, security and tool baseline documented | Current phase; 21 Accepted ADRs |
| 1 — Core Domain & Application Foundation | A tested, small end-to-end increment | Baseline ready; bounded code plan and implementation request still needed |
| 2 — Local Platform | Reproducible local execution | Actual application dependencies exist |
| 3 — Testing & Quality | Broader behavior and contract verification | Runnable application |
| 4 — Continuous Integration | Automated agreed checks | Local checks are meaningful and stable |
| 5 — Registry & Release Management | Versioned, reproducible artifacts | Packaging and release strategy selected |
| 6 — Deployment Platform Evaluation | Suitable deployment and rollback | Application, local runtime and CI work |
| 7 — Continuous Delivery | Controlled promotion | Environment and deployment model selected |
| 8 — Infrastructure as Code | Reproducible infrastructure | Hosting, state and ownership selected |
| 9 — Observability | Answer operational questions | Workloads and failure modes understood |
| 10 — Security Hardening | Validate and strengthen relevant controls | Architecture and threat model available |
| 11 — Reliability & Operations | Tested recovery and actionable procedures | Persistent data and operated components |
| 12 — Scaling & Performance | Evidence-driven capacity improvements | Workload scenarios and measurements |
| 13 — Production Readiness | Explicit readiness review | Security, recovery, deployment and operation verified |

Kubernetes, Helm, GitOps and Terraform are candidates for later evaluation, not mandatory destinations. Testing, security and observability begin with relevant increments; their dedicated phases deepen existing work.

Accepted v1 scope is defined in [scope](../product/scope.md). Scope completion and production readiness are separate milestones. No deadlines or capacity targets are assumed.

Security/testing/observability are part of every relevant implementation increment. Later dedicated phases do not postpone essential controls. [Deferred gates](decision-register.md) distinguish missing commercial input from decisions that need runtime evidence.
