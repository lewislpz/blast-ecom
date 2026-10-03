from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import boto3  # type: ignore[import-untyped]
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from moto import mock_aws

from modules.common.remote_backup import download_verified_archive, upload_verified_archive

BUCKET = "blast-ecom-test-backups"


@pytest.fixture(autouse=True)
def mock_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture(autouse=True)
def aws_s3() -> Iterator[None]:
    with mock_aws():
        yield


@pytest.fixture
def versioned_bucket() -> None:
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=BUCKET)
    client.put_bucket_versioning(
        Bucket=BUCKET,
        VersioningConfiguration={"Status": "Enabled"},
    )


@pytest.fixture(autouse=True)
def remote_settings() -> Iterator[None]:
    with override_settings(
        DEBUG=False,
        REMOTE_DATABASE_BACKUP_ENABLED=True,
        BACKUP_S3_BUCKET=BUCKET,
        BACKUP_S3_PREFIX="blast-ecom/test-backups",
        BACKUP_S3_REGION="us-east-1",
        BACKUP_S3_ENDPOINT_URL="https://s3.us-east-1.amazonaws.com",
        BACKUP_S3_ALLOW_LOCAL_HTTP=False,
        BACKUP_RETENTION_DAYS=35,
    ):
        yield


def test_remote_backup_requires_explicit_enablement() -> None:
    with override_settings(REMOTE_DATABASE_BACKUP_ENABLED=False):
        with pytest.raises(CommandError, match="disabled"):
            call_command("backup_remote_database")


def test_remote_backup_rejects_bucket_without_versioning(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "database.dump"
    archive.write_bytes(b"fictional postgresql archive")
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=BUCKET)

    with pytest.raises(CommandError, match="versioning enabled"):
        upload_verified_archive(archive, backup_id=str(uuid4()))


def test_remote_backup_upload_and_exact_version_restore_verify_encryption_and_bytes(
    tmp_path: Path,
    versioned_bucket: None,
) -> None:
    del versioned_bucket
    archive = tmp_path / "database.dump"
    contents = b"fictional PostgreSQL backup fixture\x00with binary archive data"
    archive.write_bytes(contents)
    backup_id = str(uuid4())

    receipt = upload_verified_archive(archive, backup_id=backup_id)
    restored = tmp_path / "restored.dump"
    downloaded = download_verified_archive(
        restored,
        backup_id=backup_id,
        version_id=receipt.version_id,
    )

    assert receipt.backup_id == backup_id
    assert receipt.version_id and receipt.version_id != "null"
    assert receipt.sha256 == downloaded.sha256
    assert receipt.size_bytes == len(contents)
    assert restored.read_bytes() == contents
    assert os.stat(restored).st_mode & 0o777 == 0o600
    assert datetime.fromisoformat(receipt.retention_until) > datetime.now(UTC)


def test_remote_restore_requires_an_exact_version_id(
    tmp_path: Path,
    versioned_bucket: None,
) -> None:
    del versioned_bucket
    with pytest.raises(CommandError, match="exact object version"):
        download_verified_archive(
            tmp_path / "restored.dump",
            backup_id=str(uuid4()),
            version_id="null",
        )


def test_remote_restore_rejects_source_before_allocating_temporary_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allocated = False

    def unexpected_temporary_directory() -> Path:
        nonlocal allocated
        allocated = True
        raise AssertionError("invalid restore target must be rejected before staging")

    monkeypatch.setattr(
        "modules.common.management.commands.restore_remote_database.temporary_backup_directory",
        unexpected_temporary_directory,
    )
    monkeypatch.setattr(
        "modules.common.management.commands.restore_remote_database.configured_database",
        lambda: {"name": "blast_ecom_test"},
    )

    with pytest.raises(CommandError, match="differ from the configured source"):
        call_command(
            "restore_remote_database",
            backup_id=str(uuid4()),
            version_id="version-1",
            database_name="blast_ecom_test",
        )

    assert allocated is False


def test_remote_http_endpoint_is_only_allowed_for_explicit_local_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from modules.common.remote_backup import _store_configuration

    monkeypatch.setattr("modules.common.remote_backup.settings.DEBUG", False)
    monkeypatch.setattr(
        "modules.common.remote_backup.settings.REMOTE_DATABASE_BACKUP_ENABLED", True
    )
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_BUCKET", BUCKET)
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_PREFIX", "blast-ecom/test")
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_REGION", "us-east-1")
    monkeypatch.setattr(
        "modules.common.remote_backup.settings.BACKUP_S3_ENDPOINT_URL",
        "http://127.0.0.1:5001",
    )
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_ALLOW_LOCAL_HTTP", False)

    with pytest.raises(CommandError, match="HTTPS"):
        _store_configuration()


def test_debug_mode_only_allows_explicit_loopback_s3_emulator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from modules.common.remote_backup import _store_configuration

    monkeypatch.setattr("modules.common.remote_backup.settings.DEBUG", True)
    monkeypatch.setattr(
        "modules.common.remote_backup.settings.REMOTE_DATABASE_BACKUP_ENABLED", True
    )
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_BUCKET", BUCKET)
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_PREFIX", "blast-ecom/test")
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_REGION", "us-east-1")
    monkeypatch.setattr(
        "modules.common.remote_backup.settings.BACKUP_S3_ENDPOINT_URL",
        "http://127.0.0.1:5001",
    )
    monkeypatch.setattr("modules.common.remote_backup.settings.BACKUP_S3_ALLOW_LOCAL_HTTP", True)

    assert _store_configuration().endpoint_url == "http://127.0.0.1:5001"
