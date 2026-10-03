"""Verified S3-compatible storage for PostgreSQL logical backup archives."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit
from uuid import UUID

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]
from django.conf import settings
from django.core.management.base import CommandError


class RemoteBackupError(CommandError):
    """A remote archive did not satisfy the configured safety contract."""


@dataclass(frozen=True)
class BackupReceipt:
    backup_id: str
    object_key: str
    version_id: str
    sha256: str
    size_bytes: int
    retention_until: str


@dataclass(frozen=True)
class BackupStore:
    bucket: str
    prefix: str
    region: str
    endpoint_url: str
    retention_days: int


def _store_configuration() -> BackupStore:
    if not settings.REMOTE_DATABASE_BACKUP_ENABLED:
        raise RemoteBackupError(
            "Remote database backup is disabled; explicitly configure the backup environment."
        )
    bucket = settings.BACKUP_S3_BUCKET.strip()
    prefix = settings.BACKUP_S3_PREFIX.strip().strip("/")
    region = settings.BACKUP_S3_REGION.strip()
    endpoint_url = settings.BACKUP_S3_ENDPOINT_URL.strip()
    if not bucket or not region or not prefix:
        raise RemoteBackupError("Remote backup bucket, region and prefix must be configured.")
    if any(part in {".", ".."} for part in prefix.split("/")) or "\\" in prefix:
        raise RemoteBackupError("Remote backup prefix is invalid.")
    if endpoint_url:
        parsed = urlsplit(endpoint_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise RemoteBackupError(
                "Remote backup endpoint URL must not contain credentials or query data."
            )
        is_loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        local_emulator = (
            settings.DEBUG
            and settings.BACKUP_S3_ALLOW_LOCAL_HTTP
            and parsed.scheme == "http"
            and is_loopback
        )
        if parsed.scheme != "https" and not local_emulator:
            raise RemoteBackupError("Remote backup endpoint must use HTTPS.")
        if settings.DEBUG and not local_emulator:
            raise RemoteBackupError(
                "DEBUG mode may upload remote backups only to an explicitly enabled local emulator."
            )
    elif settings.DEBUG:
        raise RemoteBackupError(
            "DEBUG mode may upload remote backups only to an explicitly enabled local emulator."
        )
    return BackupStore(
        bucket=bucket,
        prefix=prefix,
        region=region,
        endpoint_url=endpoint_url,
        retention_days=settings.BACKUP_RETENTION_DAYS,
    )


def _client(store: BackupStore) -> Any:
    return boto3.client(
        "s3",
        region_name=store.region,
        endpoint_url=store.endpoint_url or None,
    )


def _key_for(store: BackupStore, backup_id: str) -> str:
    try:
        canonical_id = str(UUID(backup_id))
    except (TypeError, ValueError) as exc:
        raise RemoteBackupError("Backup ID must be a UUID.") from exc
    return f"{store.prefix}/{canonical_id}.dump"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_versioned(client: Any, *, bucket: str) -> bool:
    try:
        return bool(client.get_bucket_versioning(Bucket=bucket).get("Status") == "Enabled")
    except (BotoCoreError, ClientError):
        return False


def upload_verified_archive(archive: Path, *, backup_id: str) -> BackupReceipt:
    """Upload only to a versioned bucket and verify encryption, metadata and bytes."""
    store = _store_configuration()
    key = _key_for(store, backup_id)
    if not archive.is_file() or archive.is_symlink():
        raise RemoteBackupError("Backup archive must be a regular file.")
    size = archive.stat().st_size
    if size <= 0:
        raise RemoteBackupError("Refusing to upload an empty backup archive.")
    digest = _sha256(archive)
    created_at = datetime.now(UTC)
    retention_until = created_at + timedelta(days=store.retention_days)
    created_text = created_at.isoformat(timespec="seconds")
    retention_text = retention_until.isoformat(timespec="seconds")
    client = _client(store)
    try:
        if not _is_versioned(client, bucket=store.bucket):
            raise RemoteBackupError("Remote backup bucket must have versioning enabled.")
        with archive.open("rb") as stream:
            response = client.put_object(
                Bucket=store.bucket,
                Key=key,
                Body=stream,
                ContentLength=size,
                ContentType="application/vnd.postgresql.backup",
                ServerSideEncryption="AES256",
                Metadata={
                    "backup-id": str(UUID(backup_id)),
                    "created-at": created_text,
                    "retention-until": retention_text,
                    "sha256": digest,
                },
                Tagging=urlencode(
                    {
                        "purpose": "database-backup",
                        "retention-until": retention_text,
                    }
                ),
            )
        version_id = str(response.get("VersionId") or "")
        if not version_id or version_id == "null":
            raise RemoteBackupError("Object storage did not return a non-null version ID.")
        head = client.head_object(Bucket=store.bucket, Key=key, VersionId=version_id)
        metadata = head.get("Metadata", {})
        if (
            head.get("VersionId") != version_id
            or head.get("ServerSideEncryption") != "AES256"
            or head.get("ContentLength") != size
            or metadata.get("backup-id") != str(UUID(backup_id))
            or metadata.get("sha256") != digest
            or metadata.get("created-at") != created_text
            or metadata.get("retention-until") != retention_text
        ):
            raise RemoteBackupError("Remote backup verification metadata did not match the upload.")
        tag_set = client.get_object_tagging(
            Bucket=store.bucket,
            Key=key,
            VersionId=version_id,
        ).get("TagSet", [])
        tags = {tag.get("Key"): tag.get("Value") for tag in tag_set}
        if (
            tags.get("purpose") != "database-backup"
            or tags.get("retention-until") != retention_text
        ):
            raise RemoteBackupError("Remote backup retention tags could not be verified.")
        remote = client.get_object(Bucket=store.bucket, Key=key, VersionId=version_id)
        remote_digest = hashlib.sha256()
        with remote["Body"] as body:
            for chunk in iter(lambda: body.read(1024 * 1024), b""):
                remote_digest.update(chunk)
        if remote_digest.hexdigest() != digest:
            raise RemoteBackupError("Remote backup checksum did not match the local archive.")
    except RemoteBackupError:
        raise
    except (BotoCoreError, ClientError, OSError) as exc:
        raise RemoteBackupError(
            f"Remote backup upload or verification failed ({type(exc).__name__})."
        ) from None
    return BackupReceipt(
        backup_id=str(UUID(backup_id)),
        object_key=key,
        version_id=version_id,
        sha256=digest,
        size_bytes=size,
        retention_until=retention_text,
    )


def download_verified_archive(
    destination: Path,
    *,
    backup_id: str,
    version_id: str,
) -> BackupReceipt:
    """Download one exact encrypted object version and verify its bytes before restore."""
    store = _store_configuration()
    key = _key_for(store, backup_id)
    if destination.exists() or destination.is_symlink():
        raise RemoteBackupError("Refusing to overwrite an existing restore archive path.")
    if not version_id or version_id == "null" or len(version_id) > 1024:
        raise RemoteBackupError("Restore requires a non-null exact object version ID.")
    client = _client(store)
    try:
        if not _is_versioned(client, bucket=store.bucket):
            raise RemoteBackupError("Remote backup bucket must have versioning enabled.")
        head = client.head_object(Bucket=store.bucket, Key=key, VersionId=version_id)
        metadata = head.get("Metadata", {})
        if (
            head.get("VersionId") != version_id
            or head.get("ServerSideEncryption") != "AES256"
            or metadata.get("backup-id") != str(UUID(backup_id))
            or not re.fullmatch(r"[0-9a-f]{64}", metadata.get("sha256", ""))
            or not metadata.get("retention-until")
            or int(head.get("ContentLength", 0)) <= 0
        ):
            raise RemoteBackupError("Selected remote backup version failed metadata verification.")
        tags = client.get_object_tagging(
            Bucket=store.bucket,
            Key=key,
            VersionId=version_id,
        ).get("TagSet", [])
        tag_map = {tag.get("Key"): tag.get("Value") for tag in tags}
        if (
            tag_map.get("purpose") != "database-backup"
            or tag_map.get("retention-until") != metadata["retention-until"]
        ):
            raise RemoteBackupError("Selected remote object is not tagged as a database backup.")
        response = client.get_object(Bucket=store.bucket, Key=key, VersionId=version_id)
        digest = hashlib.sha256()
        size = 0
        with destination.open("wb") as output, response["Body"] as body:
            os.chmod(destination, 0o600)
            for chunk in iter(lambda: body.read(1024 * 1024), b""):
                output.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        expected_size = int(head["ContentLength"])
        expected_digest = metadata["sha256"]
        if size != expected_size or digest.hexdigest() != expected_digest:
            destination.unlink(missing_ok=True)
            raise RemoteBackupError("Downloaded backup checksum or size did not match metadata.")
    except RemoteBackupError:
        raise
    except (BotoCoreError, ClientError, OSError, ValueError) as exc:
        destination.unlink(missing_ok=True)
        raise RemoteBackupError(
            f"Remote backup download or verification failed ({type(exc).__name__})."
        ) from None
    return BackupReceipt(
        backup_id=str(UUID(backup_id)),
        object_key=key,
        version_id=version_id,
        sha256=expected_digest,
        size_bytes=size,
        retention_until=metadata["retention-until"],
    )


def configured_database() -> dict[str, str]:
    database = settings.DATABASES["default"]
    if database.get("ENGINE") != "django.db.backends.postgresql":
        raise RemoteBackupError("Remote backup commands require PostgreSQL.")
    return {
        "host": str(database.get("HOST", "") or "localhost"),
        "port": str(database.get("PORT", "5432")),
        "user": str(database.get("USER", "")),
        "password": str(database.get("PASSWORD", "")),
        "name": str(database["NAME"]),
    }


def create_new_restore_database(target_name: str, *, source: dict[str, str]) -> None:
    validate_restore_database_target(target_name, source=source)
    from django.db import connections

    connection = connections["default"]
    previous_autocommit = connection.get_autocommit()
    try:
        connection.set_autocommit(True)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [target_name])
            if cursor.fetchone() is not None:
                raise RemoteBackupError("Restore target already exists; refusing to modify it.")
            cursor.execute(f"CREATE DATABASE {connection.ops.quote_name(target_name)}")
    finally:
        connection.set_autocommit(previous_autocommit)


def validate_restore_database_target(target_name: str, *, source: dict[str, str]) -> None:
    if re.fullmatch(r"[a-z][a-z0-9_]{0,62}", target_name) is None:
        raise RemoteBackupError("Target database name must be a valid PostgreSQL identifier.")
    if target_name == source["name"]:
        raise RemoteBackupError("Restore target must differ from the configured source database.")


def restore_database_config(source: dict[str, str], *, target_name: str) -> dict[str, str]:
    return {**source, "name": target_name}


def temporary_backup_directory() -> Path:
    """Create a private process-specific temporary directory for archive staging."""
    import tempfile

    path = Path(tempfile.mkdtemp(prefix="blast-ecom-remote-backup-"))
    os.chmod(path, 0o700)
    return path


def remove_temporary_directory(path: Path) -> None:
    shutil.rmtree(path)
