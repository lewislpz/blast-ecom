# Tooling and Compatibility Baseline

Status: Accepted choices; no packages installed, manifests or lockfiles generated. [ADR-0019](../decisions/ADR-0019-tooling-and-local-development.md).

## Runtime Lines

| Component | Baseline | Reason |
|---|---|---|
| Python | 3.13, supported patch at implementation | Compatible with selected Django/DRF lines |
| Django | 5.2 LTS, latest supported patched release within line | Stability/support window instead of newest feature release |
| DRF | 3.16, supported patched release | Documented Django 5.2/Python 3.13 compatibility |
| PostgreSQL | 17, supported patched release | Supported relational baseline; no feature requires a newer major |
| Node.js | 24 LTS, patched release | Frontend tool runtime |
| React | 19 | Current major baseline; compatible tool resolution required |
| Vite / TypeScript | Supported stable releases compatible with above | Exact versions depend on scaffold-time resolution |

This is not a verified lock set. Resolve full versions, inspect package engine/peer requirements, generate lockfiles and run startup/build/tests before reporting compatibility achieved. If a selected line loses support or conflicts with a necessary dependency, document the change before adoption. No prereleases or bare latest image tags.

## Dependency and Quality Tools

| Tool | Responsibility |
|---|---|
| uv + uv.lock | Python environments/dependency locking; future verification uses locked resolution |
| npm + package-lock.json | One frontend project; future reproducible installs use npm ci |
| psycopg 3 | PostgreSQL driver for Django |
| drf-spectacular | OpenAPI generation |
| openapi-typescript | Frontend contract types |
| Ruff | Python lint and formatting |
| mypy + django-stubs | Backend type checks; strict application boundaries, explicit exceptions for framework-generated surfaces |
| TypeScript strict + ESLint + Prettier | Frontend typing, correctness lint and formatting |
| pytest + pytest-django | Backend unit/integration/API tests |
| Vitest + React Testing Library | UI/component behavior |
| Playwright | Few complete browser journeys |

Only add a tool when its implementation slice uses it. No generic shared package, Nx/Turborepo, Redux or dual formatter stack for Python.

## Git and Review Policy

GitHub Flow as future convention: main, short-lived changes, Conventional Commits, squash merge. Every significant change includes tests/doc updates and ADR changes if required. A second review is required for high-risk changes under repository rules; ordinary solo work uses an explicit self-review, not a fabricated approval. Required CI statuses/branch protection configured only once checks and repository exist.

No Git repository was initialized and no commit/push occurred in Phase 0.

## Sources

[Django support](https://www.djangoproject.com/download/), [Python compatibility](https://docs.djangoproject.com/en/5.2/faq/install/), [DRF 3.16](https://www.django-rest-framework.org/community/3.16-announcement/), [Node releases](https://nodejs.org/en/about/previous-releases), [PostgreSQL support](https://www.postgresql.org/support/versioning/), [uv lock behavior](https://docs.astral.sh/uv/concepts/projects/sync/).

Tool references: [Ruff](https://docs.astral.sh/ruff/), [django-stubs](https://github.com/typeddjango/django-stubs), [openapi-typescript](https://openapi-ts.dev/introduction), [psycopg](https://www.psycopg.org/psycopg3/docs/), [TypeScript strict](https://www.typescriptlang.org/tsconfig/strict.html), [Compose](https://docs.docker.com/compose/).
