# ADR-0022: Frontend OpenAPI Type Generator

## Status

Accepted

## Date

2026-09-30

## Context

The approved frontend conventions require generated TypeScript API types from the reviewed backend OpenAPI document. The frontend compiler is TypeScript 6.0.3. The planned `openapi-typescript` 7.13.0 declares a TypeScript 5-only peer range, so npm correctly rejects that combination. Version 6.7.6 installs, but brings an `undici` version with high-severity advisories. Forcing npm peer resolution or accepting known vulnerable code-generation dependencies would weaken reproducibility and supply-chain hygiene.

## Decision Drivers

- Preserve TypeScript 6.0.3 and its existing strict compiler configuration.
- Generate committed types reproducibly from `backend/openapi.yaml`.
- Avoid generating an unused HTTP SDK or runtime schemas.
- Keep generated output read-only to feature code.
- Resolve the generator toolchain with no known npm audit findings.

## Options Considered

### Option A — Keep openapi-typescript 7 and downgrade the project compiler

Advantages:

- Remains aligned with the original generator selection.
- Straightforward generation command.

Disadvantages:

- Changes the established TypeScript 6 toolchain solely to satisfy one dev tool.
- Requires revalidating all compiler and lint assumptions.

### Option B — Use openapi-typescript 6.7.6 with TypeScript 6

Advantages:

- Minimal migration and output is compatible with the current app.

Disadvantages:

- Older generator dependency tree includes vulnerable `undici`.
- Avoids the newer package's peer declaration without resolving its intended compatibility boundary.

### Option C — Use @hey-api/openapi-ts with only its TypeScript plugin

Advantages:

- Declares support for TypeScript 6 and Node.js 22+.
- Can emit schema types only, retaining the small hand-written same-origin fetch adapter.
- Current lock resolves without known npm audit findings after pinning transitive `js-yaml` to patched 4.3.2.

Disadvantages:

- Different generated type names and output format require a small integration change.
- The explicit transitive override must be reviewed when updating the generator.

## Decision

Use `@hey-api/openapi-ts` with only the `@hey-api/typescript` plugin, reading `../backend/openapi.yaml` into `frontend/src/shared/api/generated/`. Keep `package-lock.json` authoritative, retain the `js-yaml` 4.3.2 override until the upstream dependency range includes a patched release, and verify generation is clean after running `npm run generate:api-types`. Do not generate or add an SDK/client runtime; the application continues using its small same-origin fetch adapter.

This choice was made under the owner's explicit delegation to proceed with recommended cohesive implementation decisions while continuing the approved first slice.

## Consequences

### Positive

- The generated request and response types compile under the accepted TypeScript 6 toolchain.
- No known npm audit vulnerabilities are present in the locked frontend dependency graph at acceptance time.
- The runtime API client remains small and preserves existing CSRF, cookie, error and idempotency behavior.

### Negative

- Generated output differs from the originally planned `openapi-typescript` layout.
- The package override adds a small maintenance obligation during dependency updates.

### Risks

- Future generator upgrades may change naming/output or remove the need for the override; regenerate, review diffs, run type/tests/audit, and revise this ADR when that happens.
- Tooling vulnerability status changes over time; rerun `npm audit` during dependency updates.

## Related Decisions

- [ADR-0018: Frontend State and UI Conventions](ADR-0018-frontend-conventions.md) (superseded only for the generator choice).
- [ADR-0019: Tooling and Local Development](ADR-0019-tooling-and-local-development.md).

## Notes

The pinned generator version is resolved through `frontend/package-lock.json`. The package declaration is range-based for ordinary compatible updates; every lock update requires clean installation, generation-diff, audit and frontend verification.
