# Database Backup and Restore

Status: **Implemented for local S3-compatible testing; hosted configuration and recovery are not yet validated.**

## Remote workflow

The Django management commands `backup_remote_database` and `restore_remote_database` implement an opt-in PostgreSQL logical archive workflow. It uses PostgreSQL `pg_dump`/`pg_restore` custom-format archives and an S3-compatible object API. See [ADR-0031](../decisions/ADR-0031-versioned-remote-database-backups.md).

Backup refuses to run unless `BLAST_ECOM_REMOTE_BACKUP_ENABLED=true`, a bucket, region and prefix are configured, and bucket versioning reports `Enabled`. It uploads with SSE-S3 (`AES256`), records backup ID, creation time, SHA-256 and a retention timestamp as metadata, and adds descriptive purpose/retention tags. Before printing success, it reads the exact returned object version back and verifies version, encryption, metadata, tags, length and SHA-256.

Restore requires the printed backup ID and exact non-null version ID. It verifies metadata/tags and downloaded bytes, validates the PostgreSQL archive, and restores transactionally into a new database. It rejects the configured source database, unsafe identifiers and an already-existing target. It does not overwrite or drop databases.

Example commands (after configuration):

```sh
cd backend
uv run python manage.py backup_remote_database
uv run python manage.py restore_remote_database \
  --backup-id <backup-id> \
  --version-id <exact-object-version> \
  --database-name blast_ecom_restore_drill
```

The backup command prints the backup ID, object key, version ID, size, checksum and retention timestamp only after verification. Treat this output as operationally sensitive metadata and store it in the approved operations record, not in a public issue.

## Configuration and permissions

Remote backup is disabled by default. Configure the `BLAST_ECOM_BACKUP_*` variables in `.env.example` only in the execution environment; never commit credentials. Production should use HTTPS and a narrowly scoped workload identity/default credential provider. Do not embed keys in the endpoint URL or command line.

The bucket must be private, versioned, encrypted, and protected by reviewed policy. The application requests and verifies SSE-S3, but it does not create or validate bucket policy, public-access blocks, IAM scope, deletion protection, replication, or lifecycle configuration. Retention metadata and tags are not retention enforcement: configure a reviewed lifecycle rule for current and noncurrent object versions and test it separately. The configured number of retention days is descriptive metadata only until such a rule is applied.

## Local test configuration

The integration drill uses a disposable Moto S3 API endpoint and PostgreSQL database. HTTP endpoints are accepted only for an explicitly opted-in loopback emulator while Django `DEBUG` is enabled. A local emulator test proves the application workflow against its S3 API model, not against a hosted provider or its IAM, lifecycle, durability, or availability behavior.

## Temporary data and operational limitations

The custom-format dump is plaintext while stored in a private (`0700` directory, `0600` file) temporary directory. Restore downloads the archive to a similarly protected file. Cleanup removes the temporary directory but does not claim secure media erasure. Hosted execution must use protected, capacity-managed, preferably encrypted ephemeral storage, isolate the process and ensure crash cleanup. This must be addressed before real customer data is backed up.

No hosted bucket, production credentials, lifecycle policy, alert, scheduled backup, recovery objective, or hosted restore has been configured or validated. No RPO/RTO, availability, disaster-recovery, or production-readiness claim is made. A completed command is one logical backup/restore operation; scheduling, retention enforcement, monitoring and restore drills remain deployment responsibilities.

## Recovery drill

1. Select a backup ID and exact version from a verified backup receipt.
2. Restore to a new isolated database; never use the configured source name.
3. Run migration/schema and representative integrity checks against the restored database.
4. Record the source version, restore duration, validation results, and cleanup/retention disposition in a controlled operations record.
5. Do not claim an RPO/RTO until repeated drills measure them in the selected hosted environment.
