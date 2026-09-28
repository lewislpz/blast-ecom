# ADR-0019: Tooling and Local Development

## Status

Accepted

## Date

2026-09-28

## Context

A reproducible implementation needs compatible runtime lines and a small set of tools, not deployment infrastructure.

## Decision Drivers

Cohesion with ADR-0001 through ADR-0012, correctness, manageable development/operations, explicit contracts and avoidance of speculative infrastructure.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Native app processes plus Compose PostgreSQL | Fast local edit/reload and real database semantics | Host runtimes must be managed |
| Everything containerized immediately | Uniform runtime | More initial packaging and reload setup |
| Host-installed database only | No container dependency | Higher local configuration drift |

## Decision

Use Python 3.13, Django 5.2 LTS, DRF 3.16, PostgreSQL 17, Node.js 24 LTS and React 19 as baseline lines. Select compatible stable Vite/TypeScript/tool releases and exact patched versions at scaffolding with lock resolution and smoke tests. Use uv with uv.lock for Python; npm with package-lock.json for the single frontend; psycopg 3 as Django's PostgreSQL driver.

Use backend/ and frontend/ roots in the monorepo. Initial local Compose runs PostgreSQL only; Django, Vite and the maintenance command run as host processes. Vite proxies /api and /admin to Django. Select Ruff formatting/lint, mypy with django-stubs for backend checks, TypeScript strict mode plus ESLint/Prettier for frontend. No Nx/Turborepo or application Dockerfile before useful app code. No packages or configuration are created in Phase 0.

## Approval and Provenance

Decision maker: Codex, under the project owner's explicit authorization on 2026-09-28 to advance recommended decisions autonomously and report the result. This is delegated acceptance, not a claim that the user individually selected each detail. The earlier per-decision confirmation rule is waived for this round only. No implementation or production deployment is authorized.

## Consequences

The chosen direction reduces initial integration and operational work relative to the alternatives. It constrains the first implementation and requires verification before any runtime claim.

Risk: Version-family compatibility is informed by official docs, not a tested lock set. Exact supported patch resolution is a required implementation gate.

## Reversibility

Low to moderate for tooling, moderate for major runtime upgrades.

## Reconsideration Trigger

Unsupported versions, resolver conflicts, collaboration needs or a deployment milestone.

## Related Decisions and Specifications

- [tooling](../development/tooling.md).
- [local-development](../development/local-development.md).
- [Decision index](README.md).

## Notes

All behavior is an accepted design, not implemented functionality. Configurable defaults are provisional product assumptions, not measured targets. Public use requires the gates in the security baseline and decision register.
