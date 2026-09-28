# Architecture Principles

These principles derive from the user's master project instructions.

1. Significant architectural choices require explicit user selection or explicit delegated decision authority, with ADR provenance. Delegation is scoped to the authorized round.
2. Prefer the simplest design that satisfies real requirements; add technology for a stated problem.
3. Keep domain responsibility distinct from runtime deployment and repository organization.
4. Maintain explicit contracts and clear ownership; concrete enforcement mechanisms remain to be selected.
5. Separate interface concerns, business rules and persistence responsibilities without imposing a framework.
6. Consider security, testability, observability, rollback and operation with each relevant increment.
7. Measure performance and capacity before optimizing or claiming scalability.
8. Describe future capabilities as planned; never claim controls or integrations that do not exist.
9. Preserve historical decisions and record consequences, risks and reconsideration triggers.
10. A deliberately simple solution is not automatically technical debt. Record an accepted compromise when it creates a known future obligation.

Initial priorities: correctness, security and maintainability, then operability and responsive user journeys. Numeric availability targets, recovery objectives and capacity requirements remain pending real workload/business input. A modular monolith does not guarantee painless service extraction.
