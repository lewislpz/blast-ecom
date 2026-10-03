# ADR-0031: Versioned Remote Database Backups

## Status

Accepted

## Date

2026-10-03

## Context

The existing PostgreSQL custom-format backup commands protect only a local development database. Hosted recovery requires a separately stored archive and a repeatable restore procedure. No cloud provider, account, bucket, credentials, recovery objective, or production retention policy has been selected or provisioned.

## Decision Drivers

- A backup must not be reported successful until the remote object can be read back and verified.
- Restores must select an exact immutable object version and must not overwrite the source or an existing database.
- Provider-specific infrastructure must remain deferred until a hosted environment is selected.
- Credentials must come from the runtime's external credential provider, not source control.
- Local behavior must remain opt-in and testable without a cloud account.

## Options Considered

### Cloud-provider-native snapshots

Use a managed database snapshot service and provider-native lifecycle controls.

Advantages:

- Managed point-in-time recovery and lifecycle may be available.
- Avoids creating logical dumps on the application host.

Disadvantages:

- Couples the backup workflow to a provider and managed database that have not been chosen.
- Cannot be exercised in the current local environment.

### S3-compatible logical archive workflow

Create a PostgreSQL custom-format dump, upload it through the S3 API, and restore a selected version into a fresh database.

Advantages:

- Provider-independent API with a disposable local emulator for an end-to-end drill.
- Explicit checksum, server-side encryption, version selection, and restore controls.

Disadvantages:

- Requires PostgreSQL client tools and temporary local disk space containing plaintext database data.
- Metadata and tags do not enforce retention; bucket lifecycle and access policy remain external configuration.
- Does not provide point-in-time recovery by itself.

## Decision

Implement the S3-compatible logical archive workflow as an opt-in application operation. Require HTTPS outside DEBUG, require bucket versioning, request SSE-S3 (`AES256`), and verify object metadata, tags, version, size, encryption, and downloaded SHA-256 before reporting success or restoring. Use the default AWS-compatible credential chain. Restore requires an exact non-null version and creates a new, absent target database distinct from the configured source. Do not select a provider, provision a bucket, or claim hosted recovery readiness in this ADR.

Retention timestamps and object tags are descriptive verification data only. A reviewed bucket lifecycle policy must enforce expiry; provider policy, deletion protection, and backup/restore permissions must be independently configured and tested before hosted use.

## Consequences

### Positive

- Backup artifacts are remotely read back and checksum-verified before success is reported.
- Version-specific restore and fresh-target rules reduce accidental overwrite risk.
- The API can be integration-tested locally without cloud credentials.

### Negative

- Dump creation and restore stage plaintext locally in a mode-restricted temporary directory; this requires protected, capacity-managed, preferably ephemeral storage in hosted operation.
- This is a logical backup workflow, not continuous protection; RPO/RTO and recovery coverage are unknown.
- Lifecycle expiry, IAM policy, bucket privacy, immutability, monitoring, and credential delivery are not provisioned by application code.

### Risks

- An overly broad runtime credential could read, overwrite, or delete unrelated objects; hosted credentials must be narrowly scoped and reviewed.
- Bucket lifecycle misconfiguration can retain backups too long or delete them too early.
- Emulator success does not establish compatibility with a selected hosted provider.
- Local disk exhaustion or compromise can expose or interrupt backup/restore.

## Related Decisions

- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)
- [ADR-0027: Safe Local PostgreSQL Backup and Restore](ADR-0027-local-postgresql-backup-and-restore.md)

## Notes

Revisit provider-native snapshots, WAL archiving, encryption-key ownership, immutable retention, lifecycle, and recovery objectives after the hosting provider and data requirements are selected.
