# ADR-0018: Frontend State and UI Conventions

## Status

Accepted

## Date

2026-09-28

## Context

React/TypeScript/Vite is accepted; routing, server state and forms need bounded choices.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| React Router, TanStack Query, native forms and CSS Modules | Explicit route/server/UI state separation | Two focused runtime dependencies |
| Handwritten navigation and fetch effects | Fewer dependencies | Repeated loading/cache/error logic |
| Full UI/state framework suite | Many prebuilt features | Premature state and design-system commitments |

## Decision

Use React Router in declarative mode, TanStack Query for server state, a small fetch wrapper with credentials/CSRF/error handling, native controlled forms and CSS Modules with shared CSS variables. Use component state and a small cart context; no Redux, persistent cart or UI component suite initially.

The cart stores product IDs and quantities only, remains in memory and resets on reload/logout. The backend owns price/stock truth. Generate TypeScript API types from OpenAPI using openapi-typescript; do not duplicate domain rules in React. Disable blind mutation retries. Provide loading, empty, error, success and keyboard-accessible states. Document Vite SPA search visibility limits; server rendering is deferred until a public acquisition need is established.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: Stale catalog data must not cause silent price changes; explicit checkout conflict handling required. No SEO performance claim.

## Reversibility

Easy to moderate for styles/forms; moderate for routing and server-state migration.

## Reconsideration Trigger

Measured UX/state complexity, reusable design needs or real search acquisition requirements.

## Related Decisions and Specifications

- [frontend](../development/frontend.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
