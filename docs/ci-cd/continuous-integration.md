# Continuous Integration

Status: **Workflow implemented locally; hosted GitHub Actions execution and repository settings are pending.**

## Workflow boundary

`.github/workflows/ci.yml` runs on pull requests, pushes to `main`, and manual dispatch. It uses `pull_request`, not `pull_request_target`, grants only `contents: read`, and does not configure secrets, registry login, image push, deployment, or workflow writes. External actions are pinned to full commit SHAs. The exact upstream release references are documented inline in the workflow.

Pull-request code is untrusted, including same-repository branches. The workflow builds and scans PR images locally on the disposable runner but does not upload them. A push to `main` exports the already-built API and storefront images as compressed tar archives in one commit-addressed Actions artifact, with 30-day workflow-artifact retention. The workflow itself cannot prove that the push was reviewed: repository owners must enable branch protection, required checks, and reviews before treating these artifacts as reviewed candidates. Until then, do not promote them. The workflow makes no claim that this is a permanent release artifact.

## Checks

The backend job installs `backend/uv.lock`, uses a disposable PostgreSQL service, and runs Ruff, formatting, mypy, Django system checks, migration drift checks, validated OpenAPI generation plus exact schema diff, and the complete pytest suite. The frontend job uses `npm ci` against `package-lock.json`, runs typecheck/lint/format/tests, an npm audit that blocks HIGH or CRITICAL advisories, and a production build.

After both pass, the image job builds the `production` targets and scans source lockfiles/configuration plus each image with Trivy 0.74.0; the scanner database remains current at run time. HIGH/CRITICAL findings fail by default, including vulnerabilities without a published fix. Only the API image vulnerability scan may apply exact, temporary Debian 13 OS-package exceptions listed in `.github/security/trivy-accepted-image-risks.json`; the checker matches CVE, package, installed version, result type/class and distro, and fails on malformed, expired, stale or unmatched entries. Accepted findings remain visible in the job output with owner and expiry. Source scans, secrets, misconfigurations and frontend image findings remain fully blocking. Trivy JSON reports stay in runner temporary storage and secret match contents are never printed. No source or image scan guarantees absence of vulnerabilities. The Python production image applies current signed Debian security updates at build time and omits `pip`/`ensurepip` from the final runtime; the Nginx production image applies current signed Alpine package updates while retaining its unprivileged runtime user.

Local production-image scans using Trivy 0.74.0 after these updates returned zero HIGH/CRITICAL findings for the storefront. The API scan reports 44 package/advisory tuples across eight Debian 13 CVEs. These remain scanner findings, not false positives or fixed vulnerabilities; a 30-day exact exception set is recorded in ADR-0033 and remains visible during CI. It expires 2026-11-03 and must be re-triaged earlier if packages, scanner data or runtime privileges change. The policy checker and current local scan are under verification; the workflow has not run on GitHub or on amd64.

## Production image targets

- API: non-root Python image running Gunicorn/WSGI. Django static files are collected at build time and served by WhiteNoise. The final image does not include pip or ensurepip.
- Storefront: static Vite build served by an unprivileged Nginx image on port 8080. Current signed Alpine package updates are applied at build time. SPA route fallback is enabled. Its `/health/ready/` endpoint checks only the static HTTP container, not API or database readiness.

The Compose service topology is unchanged; the Python development target shares the refreshed Debian base. A hosted deployment still needs deliberate ingress/path routing for same-origin `/api/`, `/admin/`, `/health/` and `/static/` requests, trusted proxy configuration, secrets/TLS, database migrations, probes and rollback. This workflow does not supply that topology.

## Artifacts and later promotion

Artifact names use the full source commit SHA; upload-artifact provides immutability within each workflow run. Both images are exported from the same successful build job; later promotion should consume those archives rather than rebuild. They are retained for 30 days and are not pushed to GHCR. A registry, signed provenance/SBOM, release tagging and longer retention are deferred until delivery requirements are selected.

## Host setup and validation status

After the workflow is present on the repository's default branch, configure branch protection to require the `Backend checks`, `Frontend checks`, and `Build and scan production images` job results (confirm the exact UI check names after the first hosted run). Require review for changes to `.github/workflows/**`, Dockerfiles and dependency locks. GitHub Actions must be enabled by repository owners.

No hosted Actions run, branch-protection rule or required-check enforcement has been verified in this workspace. Local checks and Docker builds validate the workflow inputs but do not replace a hosted run.
