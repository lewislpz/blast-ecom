# ADR-0033: Temporary Debian Image Risk Acceptance

## Status

Accepted

## Date

2026-10-04

## Decision Authority

Selected under the user's explicit autonomous-completion delegation on 2026-10-04. Independent code review is a required implementation gate before this policy is treated as verified.

## Context

After refreshing the production Python base image, Trivy 0.74.0 still reports 44 HIGH findings across eight CVE IDs in Debian 13 OS packages in the API image. Current Debian tracker records continue to mark these Trixie issues vulnerable, with no-DSA/minor, postponed, or planned-point-release status. These classifications inform triage but do not prove the vulnerable code is unreachable or harmless. The frontend image has no HIGH/CRITICAL findings. The existing scanner blocks every HIGH/CRITICAL item, leaving the API image CI policy red despite exact package and advisory triage.

The local API runs as a non-root UID. Development Compose drops all Linux capabilities and enables `no-new-privileges`; the production image alone does not enforce those runtime controls. Consequently, image acceptance is not authorization to deploy. Production remains gated until a hosted runtime proves least privilege, networking, monitoring and recovery requirements.

## Decision Drivers

- Preserve strict blocking for new or unreviewed HIGH/CRITICAL findings.
- Do not hide secrets, misconfigurations, frontend findings, language dependencies, other distributions, or different package versions.
- Make accepted risk visible in CI output, owned, evidence-linked and time-limited.
- Fail closed on malformed, expired, broad, stale or unmatched policy entries.
- Keep the change easy to reverse when Debian publishes fixes or risk assessment changes.

## Options Considered

### Option A — Keep all API image scans failing

Advantages:

- No acceptance exception can be misapplied.
- The original threshold remains uncomplicated.

Disadvantages:

- CI cannot distinguish the reviewed Debian stable findings from a newly introduced vulnerability.
- The application image cannot pass its configured gate until all base distribution packages are fixed upstream or the distribution changes.

Reversibility: Easy to keep; no policy code change required.

### Option B — Add exact, expiring OS-package exceptions

Advantages:

- Keeps the default HIGH/CRITICAL threshold and accepts only explicitly enumerated CVE/package/version tuples from Debian 13 OS-package results.
- Keeps every accepted finding visible with owner and expiry.
- Forces review when an accepted tuple disappears, changes version/distribution, or expires.

Disadvantages:

- The vulnerable package code remains in the image during the acceptance window.
- Policy validation itself becomes security-sensitive code and requires tests/review.
- A scanner database/vendor classification can change before expiry; recurring review is required.

Reversibility: Easy to reverse by deleting exception entries and returning the API image check to strict mode.

### Option C — Replace the image distribution or build a custom runtime

Advantages:

- Could remove some distro-specific findings without policy exceptions.

Disadvantages:

- A new base/runtime increases compatibility, patching and maintenance work and may introduce different findings.
- Prior local distroless evaluation reported more high/critical findings and an ABI/tooling migration burden.
- No measured evidence shows a replacement would be safer overall.

Reversibility: Moderately expensive; build/runtime support and operational familiarity would change.

## Decision

Keep HIGH/CRITICAL blocking by default. Adopt Option B only for the exact 44 Debian 13 OS-package/CVE/version tuples enumerated in `.github/security/trivy-accepted-image-risks.json`, initially expiring 2026-11-03. The policy checker is invoked only for the production API image vulnerability report. The exception must match CVE ID, package name, installed version, Trivy result type/class and Debian 13 distro prefix. Each CVE entry names a responsible owner, exact Debian tracker URL, review date, expiry and rationale. Every configured tuple must appear in the current report; stale entries fail until removed. Expired, malformed or unsupported policy fails closed.

The source filesystem scans, secrets and misconfiguration checks, frontend image scan, and any package/distro/version/advisory outside the exact list remain strict. Reports and accepted findings remain visible in logs without echoing secret values.

This is temporary local CI triage, not a statement that findings are false positives, fixed, or production-safe. Re-triage no later than 2026-11-03 and sooner when Debian/package updates, Trivy data, runtime privileges, architecture, or hosted CI changes. Do not deploy until production runtime capability restrictions and independent deployment review are verified.

## Consequences

### Positive

- CI can pass only for the current, exact and time-limited Debian findings while still failing for unreviewed high/critical issues.
- Accepted risk has traceable provenance and a mandatory review date.

### Negative

- The image remains vulnerable to the listed conditions during the acceptance period.
- The shared Python runtime includes low-level system libraries that are not direct application features.
- Hosted CI and amd64 results remain unverified until the workflow runs on GitHub and the production image is scanned there.

### Risks

- Container non-root execution does not eliminate kernel/system package exploit paths. In particular, hosted workloads must drop all capabilities, avoid host namespaces/mounts, and prevent untrusted tar processing before considering deployment.
- The policy checker can itself be a bypass if its schema or match criteria are weakened; changes require tests and independent review.
- The selected maintainers group must own review/removal; expired acceptance deliberately breaks CI.

## Related Decisions

- [ADR-0032: CI Security and Artifact Boundary](ADR-0032-ci-security-and-artifact-boundary.md) (superseded for scan threshold only)
- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)

## Notes

Primary Debian tracker records reviewed 2026-10-04:

- [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720)
- [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742)
- [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369)
- [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642)
- [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408)
- [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409)
- [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410)
- [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538)
