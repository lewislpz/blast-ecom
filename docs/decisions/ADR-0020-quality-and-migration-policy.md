# ADR-0020: Quality, Git and Migration Policy

## Status

Accepted

## Date

2026-09-28

## Context

Tests must establish domain correctness and migration safety before automation or delivery.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Focused unit/integration tests plus a few browser journeys | Balances feedback and realistic coverage | Requires PostgreSQL test setup |
| E2E-only validation | Checks complete flows | Slow diagnostics and weak edge-case coverage |
| Mock-only persistence testing | Fast tests | Misses transactions, constraints and real DB behavior |

## Decision

Use pytest and pytest-django, PostgreSQL integration/transaction tests, DRF contract/permission tests, Vitest with React Testing Library and a small Playwright E2E suite. Use deterministic clocks/payment outcomes. Run local checks before CI is added. Define GitHub Flow with short-lived branches, Conventional Commits and squash merging as the future workflow; no Git operations are performed now.

Migrations are reviewed and versioned with models. Generate during development, apply through one explicit controlled step per environment, never concurrently from every web replica. Test clean install and upgrade from the previous state. Use expand/contract changes; prefer forward repair. Destructive changes require specific approval and a verified backup/restore plan. Reversible migration syntax is not a promise to recover deleted data. No numeric coverage target without evidence.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: Concurrency tests can pass incorrectly if using SQLite or an enclosing TestCase transaction. Auth implementation remains high risk with independent review required by repository gates.

## Reversibility

Low to moderate for tools; historical migrations must be preserved.

## Reconsideration Trigger

CI introduction, larger teams, new failure modes or deployment changes.

## Related Decisions and Specifications

- [testing-strategy](../development/testing-strategy.md).
- [migrations](../development/migrations.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
