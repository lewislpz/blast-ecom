# ADR-0027: Safe Local PostgreSQL Backup and Restore

## Status

Accepted

## Date

2026-10-01

## Context

Local development needs a way to preserve and inspect fictional application data without implying that production backup or disaster recovery exists. PostgreSQL custom-format archives support validation and selective tooling, and the installed PostgreSQL client utilities are the canonical dump/restore tools.

## Decision Drivers

- Backup/restore must be explicit, local-only and DEBUG-only.
- A backup command must not overwrite a caller's existing file.
- Restore must never target the source or modify an existing database.
- Credentials must not appear in command output.
- Restore must run as one PostgreSQL transaction after archive validation.

## Options Considered

### Option A — Django commands wrapping PostgreSQL client tools

Use `pg_dump` custom format and `pg_restore` into a newly created, caller-named database. Refuse non-local configuration, unsafe paths, same-database targets and existing databases/files.

Advantages:

- Uses PostgreSQL's supported physical/logical backup utilities.
- Keeps the interface close to local application configuration.
- Existing databases and backups are protected from accidental overwrite.

Disadvantages:

- Requires `pg_dump`/`pg_restore` compatible client utilities on `PATH`.
- Does not provide retention, scheduling, off-site storage, encryption-key operations, RPO/RTO or recovery automation.

### Option B — Managed cloud backup service

Delegate backup scheduling and retention to a hosting provider.

Advantages:

- Can provide managed retention and point-in-time recovery when configured.

Disadvantages:

- No cloud provider or hosted database has been selected.
- Does not serve the current local development requirement.

## Decision

Use Option A for local development only. Backups are custom-format files created with restrictive permissions and a non-overwrite link operation. Restore validates the archive, creates a fresh database with a validated identifier, and uses `pg_restore --single-transaction`. The configured source database is never a restore destination.

## Consequences

### Positive

- Developers can verify a local round trip while retaining the source database.
- Existing targets are rejected before any restore operation.
- Connection passwords are passed only through the child-process environment and are not printed.

### Negative

- PostgreSQL client binaries are an additional local tool prerequisite.
- This capability is not a production backup, retention or disaster-recovery system.

### Risks

- A backup on the same machine does not protect against machine/disk loss.
- A failed restore can leave the newly created target database present but empty; use a new target name for another attempt.

## Related Decisions

- [ADR-0021: Operational Baseline and Deferred Infrastructure](ADR-0021-operations-baseline-and-deferrals.md)

## Notes

Before hosted operation, select an independently stored, encrypted backup strategy and define/test RPO and RTO. Do not treat a successful local round trip as disaster recovery.
