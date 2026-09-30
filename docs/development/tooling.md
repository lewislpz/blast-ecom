# Tooling and Compatibility Baseline

Status: The first scaffold and dependency locks are implemented and verified on macOS arm64. PostgreSQL 17 runtime connectivity and the initial migration are verified using Docker. [ADR-0019](../decisions/ADR-0019-tooling-and-local-development.md) remains the selected baseline.

## Resolved Runtime and Package Versions

| Component | Resolved version | Verification status |
|---|---:|---|
| Python | 3.13.15 | Backend environment created and used for checks |
| Django | 5.2.17 | Resolved in `backend/uv.lock`; system check passed |
| Django REST framework | 3.16.1 | Resolved and exercised by PostgreSQL-backed catalog API tests |
| psycopg | 3.3.6 | PostgreSQL 17.11 connection and migrations verified |
| PostgreSQL | 17.11 (major line 17) | Fresh migrations, connectivity, local Compose persistence, restart and readiness verified |
| Docker Engine / Compose | 29.8.1 / 5.5.1 | Installed and running; local PostgreSQL Compose service verified |
| Node.js | 24.21.0 | Official macOS arm64 archive checksum verified; used for frontend checks |
| npm | 11.19.0 | Shipped with Node 24.21.0; `npm ci` passed |
| React / React DOM | 19.3.0 | Locked in `frontend/package-lock.json` |
| Vite | 8.3.1 | Locked; production build passed |
| TypeScript | 6.0.3 | Locked; type check passed |
| Vitest | 5.0.2 | Locked; component smoke test passed |
| drf-spectacular | 0.30.0 | Locked; OpenAPI generation and validation pass |
| djangorestframework-stubs | 3.16.9 | Locked dev dependency; mypy validates DRF code |

Django 5.2.18 was not available from the package index when the lock was generated; the compatible 5.2 LTS patch 5.2.17 was selected rather than relaxing the accepted Django line. The selected DRF 3.16 minor resolves to 3.16.1. These are package resolution facts, not a claim that a newer minor would be incompatible.

The generated lockfiles pin transitive artifacts. `uv` 0.12.19 and Node/npm were provisioned in a temporary tool directory for this implementation session, not installed globally or committed. Developers should use their normal trusted runtime manager and the exact project runtime files.

## Dependency and Quality Tools

| Tool | Responsibility | Status |
|---|---|---|
| uv + `backend/uv.lock` | Python environment and dependency locking | Implemented; `uv sync --locked` resolved |
| npm + `frontend/package-lock.json` | Reproducible frontend install | Implemented; `npm ci` passed |
| psycopg 3 | PostgreSQL driver | PostgreSQL 17 connection and migration apply verified |
| Ruff | Python lint and formatting | Implemented; checks passed |
| mypy + Django/DRF stubs | Backend type checks | Implemented; strict check passed |
| pytest + pytest-django | Backend unit/integration/API tests | Implemented; catalog/inventory PostgreSQL model/API/admin tests pass |
| TypeScript strict + ESLint + Prettier | Frontend typing, lint and formatting | Implemented; checks passed |
| Vitest + React Testing Library | UI/component behavior | Implemented; storefront and API client tests pass |
| drf-spectacular | API schema generation | Implemented for catalog; reviewed schema at `backend/openapi.yaml` |
| @hey-api/openapi-ts 0.99.0 | Generate TypeScript types from reviewed OpenAPI | Implemented; TypeScript-only plugin, generated output checked in; `npm run generate:api-types` |
| Playwright Test 1.63.0 | End-to-end browser journeys | Implemented; registration, checkout, simulated payment, cancellation and order history against the local stack |
| @axe-core/playwright 4.13.0 | Browser accessibility scans | Implemented; storefront, login and registration have no critical/serious axe findings |
| Docker Compose + official `postgres:17.11-bookworm` image | Local PostgreSQL only; named persistent volume and loopback port binding | Implemented and verified; no app containers or production deployment |

Only add a tool when its implementation slice uses it. No generic shared package, Nx/Turborepo, Redux, Redis, RabbitMQ or application container is introduced here.

## Git and Review Policy

GitHub Flow remains the accepted convention: `main`, short-lived changes, Conventional Commits and squash merge. The initial implementation is committed locally on `main`; commits have not been pushed. High-risk changes require independent review and explicit approval under the repository gates.

## Official Sources

- [Django supported versions](https://www.djangoproject.com/download/) and [Python compatibility for Django 5.2](https://docs.djangoproject.com/en/5.2/faq/install/).
- [Django REST framework 3.16 compatibility](https://www.django-rest-framework.org/community/3.16-announcement/).
- [drf-spectacular supported Django/DRF versions](https://drf-spectacular.readthedocs.io/en/stable/readme.html).
- [Node.js release schedule](https://nodejs.org/en/about/previous-releases) and [v24.21.0 archive](https://nodejs.org/dist/v24.21.0/).
- [Vite requirements](https://vite.dev/guide/) and [uv lock/sync behavior](https://docs.astral.sh/uv/concepts/projects/sync/).
- [Playwright](https://playwright.dev/docs/intro) and [axe-core Playwright integration](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright).

Additional tool references: [Ruff](https://docs.astral.sh/ruff/), [django-stubs](https://github.com/typeddjango/django-stubs), [Hey API OpenAPI TypeScript](https://heyapi.dev/docs/openapi/typescript/get-started), [psycopg](https://www.psycopg.org/psycopg3/docs/), [TypeScript strict](https://www.typescriptlang.org/tsconfig/strict.html), [Compose](https://docs.docker.com/compose/).
