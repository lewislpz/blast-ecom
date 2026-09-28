# Phase 0 Delegated Decisions Report

Date: 2026-09-28. Scope: architecture/documentation only.

## Outcome

Nine new Accepted ADRs (0013–0021) establish a cohesive baseline for a local simulated first implementation. Twelve previous ADRs are preserved unchanged. Accepted choices are designs, not installed or tested application capabilities.

## Authority

The project owner explicitly authorized Codex to advance recommended decisions autonomously and report results. Codex is the decision maker for this round. No claim is made that the owner selected every value individually. No general authorization for future unrelated decisions, destructive actions or deployment is inferred.

## Main Results

- Registered checkout, one stock pool and temporary browser cart.
- Explicit order/reservation/payment states, concurrency and retry behavior.
- UUIDv4, exact EUR decimals, immutable purchase/address snapshots and defined FK/locking conventions.
- Custom Django user, database sessions, CSRF, owner checks and restricted Django admin.
- REST v1, consistent errors, OpenAPI generation, typed frontend and database-backed idempotency.
- Bounded frontend/development/test tools, local PostgreSQL Compose and explicit migration procedure.
- Structured logs, transactional audit/notification intents and restartable maintenance without a broker.
- First implementation slice and public-launch gates documented.

## Tradeoffs Accepted

Account requirement adds customer friction. Django coupling is intentional. PostgreSQL remains a shared resource. UUID indexes are larger than integer indexes. Terminal paid orders cannot be cancelled in v1; refunds remain outside scope. Django admin is internal, not a custom React admin. SPA rendering has public search limitations. A stopped maintenance process conservatively delays stock release.

## Defaults versus Facts

Reservation/session/list/body limits are adjustable defaults, not measured targets. Runtime families were researched in official docs; exact lock compatibility has not been executed. Single stock pool and local simulation defaults do not establish actual warehouse, tax or shipping arrangements.

## Deferred

See the [decision register](../roadmap/decision-register.md). Real tax/shipping policy, provider email, public account protections, privacy retention, production infrastructure, recovery targets and operational platforms require external inputs or a running system.

## Verification

Documentation verification checks local links, Markdown fences, all ADR/index entries, delegated provenance, prior ADR hashes, consistent state/route terminology and absence of changes outside allowed documentation/workspace paths. Manual scenario review covers stock contention, payment/cancel races, expiry, replay, snapshot integrity and notification failure.

The executed focused check passed for 51 Markdown documents (including the root README), 21 ADR/index records, all 12 original ADR hashes, 17 route declarations and the order-state diagram. The first twelve ADRs are byte-for-byte unchanged. Diagram structure was checked textually; no Mermaid renderer or application runtime was run.

These checks do not test Django transactions, browser behavior, security enforcement, dependency compatibility or deployment. Those are required in implementation; the [test strategy](../development/testing-strategy.md) names the relevant cases.

## Next Step

Prepare a bounded implementation plan for the [first local slice](../development/first-slice.md) when implementation is requested. Start with runtime/lock verification and the custom user migration, then domain invariants. No application source, Dockerfile, Compose file, CI pipeline or infrastructure was created in this round.
