# ADR-0007: Frontend Stack

## Status

Accepted

## Date

2026-09-28

## Context

Blast Ecom is in Phase 0 with an accepted modular monolith, monorepo and six logical domains. The core stack was presented as three separate questions.

## Decision Drivers

- Support the accepted store scope with proportionate complexity.
- Keep contracts and domain responsibilities clear.
- Make development and operation maintainable.
- Respect explicit user selection.

## Options Considered

| Option | Benefits | Costs |
|---|---|---|
| React + TypeScript + Vite | Browser-rendered UI and static build artifacts | Routing/data tools require choices; search visibility requires deliberate treatment |
| React + TypeScript + Next.js | Server/static rendering options for public product pages | More server/client, caching and deployment decisions |

## Decision

Use **React + TypeScript + Vite**.

The user selected the browser-rendered React option with TypeScript and Vite. Vite is development/build tooling, not the production application server.

## Approval

Project owner selected "2 A" in the explicit response "1 b / 2 a / 3 a" on 2026-09-28. This approves the named technologies, not implementation or unmentioned dependencies.

## Consequences

Static frontend artifacts can simplify hosting. The public catalog's discoverability remains a risk to validate; this choice does not prove SEO is unimportant. Routing, data loading, styles, admin UI delivery, hosting and versions remain undecided. No Node production server is mandated by this choice.

No capacity or performance figures are assumed. Nothing is installed or deployed by this record.

## Reversibility

Moderately expensive to expensive as routing and data loading become coupled to the implementation.

## Reconsideration Trigger

Revisit if measured or explicit public search/rendering requirements justify a different rendering approach.

## Related Decisions

- [Application Architecture](ADR-0002-application-architecture.md).
- [Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).
- [Core stack and other ADRs](README.md).

## Notes

Versions will be selected after compatibility and support checks. See [project status](../project-status.md) for open decisions.
