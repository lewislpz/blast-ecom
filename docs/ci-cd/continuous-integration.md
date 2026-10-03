# Continuous Integration

Status: **Workflow implemented locally; hosted GitHub Actions execution and repository settings are pending.**

## Workflow boundary

`.github/workflows/ci.yml` runs on pull requests, pushes to `main`, and manual dispatch. It uses `pull_request`, not `pull_request_target`, grants only `contents: read`, and does not configure secrets, registry login, image push, deployment, or workflow writes. External actions are pinned to full commit SHAs. The exact upstream release references are documented inline in the workflow.

Pull-request code is untrusted, including same-repository branches. The workflow builds and scans PR images locally on the disposable runner but does not upload them. A push to `main` exports the already-built API and storefront images as compressed tar archives in one commit-addressed Actions artifact, with 30-day workflow-artifact retention. The workflow itself cannot prove that the push was reviewed: repository owners must enable branch protection, required checks, and reviews before treating these artifacts as reviewed candidates. Until then, do not promote them. The workflow makes no claim that this is a permanent release artifact.

## Checks

The backend job installs `backend/uv.lock`, uses a disposable PostgreSQL service, and runs Ruff, formatting, mypy, Django system checks, migration drift checks, validated OpenAPI generation plus exact schema diff, and the complete pytest suite. The frontend job uses `npm ci` against `package-lock.json`, runs typecheck/lint/format/tests, an npm audit that blocks HIGH or CRITICAL advisories, and a production build.

After both pass, the image job builds the `production` targets and scans source lockfiles/configuration plus each image with Trivy. All HIGH/CRITICAL findings fail the job, including vulnerabilities without a published fix. Trivy JSON reports stay in runner temporary storage; the policy checker prints only severity, finding ID and location so secret matches are not echoed into logs. No source or image scan is a guarantee of absence of vulnerabilities.

## Production image targets

- API: non-root Python image running Gunicorn/WSGI. Django static files are collected at build time and served by WhiteNoise.
- Storefront: static Vite build served by an unprivileged Nginx image on port 8080. SPA route fallback is enabled. Its `/health/ready/` endpoint checks only the static HTTP container, not API or database readiness.

The development Docker targets and Compose stack are unchanged. A hosted deployment still needs deliberate ingress/path routing for same-origin `/api/`, `/admin/`, `/health/` and `/static/` requests, trusted proxy configuration, secrets/TLS, database migrations, probes and rollback. This workflow does not supply that topology.

## Artifacts and later promotion

Artifact names use the full source commit SHA; upload-artifact provides immutability within each workflow run. Both images are exported from the same successful build job; later promotion should consume those archives rather than rebuild. They are retained for 30 days and are not pushed to GHCR. A registry, signed provenance/SBOM, release tagging and longer retention are deferred until delivery requirements are selected.

## Host setup and validation status

After the workflow is present on the repository's default branch, configure branch protection to require the `Backend checks`, `Frontend checks`, and `Build and scan production images` job results (confirm the exact UI check names after the first hosted run). Require review for changes to `.github/workflows/**`, Dockerfiles and dependency locks. GitHub Actions must be enabled by repository owners.

No hosted Actions run, branch-protection rule or required-check enforcement has been verified in this workspace. Local checks and Docker builds validate the workflow inputs but do not replace a hosted run.
