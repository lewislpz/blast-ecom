# ADR-0032: CI Security and Artifact Boundary

## Status

Accepted

## Date

2026-10-03

## Context

Blast Ecom needs repeatable backend/frontend checks, migration and API-contract drift checks, dependency/configuration/container scans, and production image builds. GitHub Actions has not yet been run for this repository, and no container registry or deployment target has been selected. Pull requests may contain untrusted code, including contributions from forks.

## Decision Drivers

- Validate each pull request without giving its code secrets or repository write access.
- Use committed lockfiles for local and image builds.
- Detect fixed high-impact dependency/image/config issues before merge.
- Preserve a commit-addressed build artifact for later promotion, contingent on host-enforced review of `main`.
- Avoid selecting a registry, cloud provider, deploy workflow, or long-lived credential before needed.

## Options Considered

### PR checks with registry publishing

Build, scan and push images to a registry during pull request workflows.

Advantages:

- Images are immediately addressable by reviewers and downstream automation.

Disadvantages:

- Untrusted pull-request code must never receive publication credentials.
- Requires registry selection, access control, cleanup and retention before those are otherwise needed.
- A PR artifact can be confused with a reviewed/release candidate.

### Read-only PR checks and main-branch artifacts

Run checks/builds on `pull_request`; save images only for a push to `main`, identified by the full commit SHA.

Advantages:

- Fork and same-repository pull requests receive no secrets and no write permissions.
- One SHA-addressed build is reusable for later promotion without rebuilding.
- No registry or deployment credentials are needed now.

Disadvantages:

- Workflow artifacts are temporary and not a substitute for an image registry or release retention.
- Repository branch protection/required checks still require host settings and a successful hosted workflow run.
- CI compute and vulnerability database access remain dependent on GitHub-hosted runners/external services.

## Decision

Use `pull_request`, `push` to `main`, and manual dispatch; never use `pull_request_target` for executing repository code. Set `GITHUB_TOKEN` permissions to `contents: read`. Pin every external action to a verified full commit SHA. Use exact Python/Node/PostgreSQL image versions and backend/frontend lockfiles. Build explicit production image targets after application checks, and scan dependency locks/configuration/images. Block all HIGH and CRITICAL findings, including findings that do not yet have a published fix; triage must happen before merge.

Keep Trivy JSON output in ephemeral runner storage and summarize only finding identifiers/severity/location. Never print secret match contents in workflow logs.

Do not log in to or push to a container registry and do not deploy. Save API and frontend OCI archives as one commit-addressed Actions artifact named with the complete commit SHA only on pushes to `main`, with 30-day retention. Upload-artifact immutability is scoped to each workflow run. The workflow cannot establish that a main push was reviewed; owners must configure branch protection, reviews and required checks before artifacts are treated as reviewed candidates. PR builds are scanned but not uploaded. This is a build artifact, not a signed/release artifact or production approval.

## Consequences

### Positive

- Untrusted PR code has only read permissions and no repository secrets/publication path.
- Backend, frontend, migrations, OpenAPI contract and production build are checked before downstream release work.
- Main-branch images are built once and have a commit-addressed artifact name; review trust depends on repository protection settings.

### Negative

- Action SHAs require deliberate dependency updates; provenance review remains necessary.
- Temporary Actions artifacts expire and must later be promoted to an explicitly selected registry.
- HIGH/CRITICAL scan threshold may need adjustment based on observed false positives and project risk tolerance.
- GitHub repository settings, required status checks, artifact retention policy and hosted run are outside this local implementation.

### Risks

- SHA pinning prevents tag movement but does not replace reviewing action source, nested actions, release provenance and permissions.
- A compromised dependency or build tool can still affect a read-only artifact build.
- Base-image patch tags can change upstream; production artifacts are commit-addressed, but bit-for-bit reproducibility is not claimed.

## Related Decisions

- [ADR-0020: Quality, Git and Migration Policy](ADR-0020-quality-and-migration-policy.md)
- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)

## Notes

This repository contains workflow configuration, but no hosted GitHub Actions run or branch protection is verified until the workflow is enabled in the actual repository. See [CI documentation](../ci-cd/continuous-integration.md).
