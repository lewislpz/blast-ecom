from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import override_settings

from modules.common.local_database import is_local_database_host


def test_compose_database_hostname_requires_explicit_local_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BLAST_ECOM_ALLOW_LOCAL_CONTAINER_DATABASE", raising=False)
    assert not is_local_database_host("postgres")
    monkeypatch.setenv("BLAST_ECOM_ALLOW_LOCAL_CONTAINER_DATABASE", "true")
    assert is_local_database_host("postgres")
    assert not is_local_database_host("remote-postgres.internal")


@override_settings(DEBUG=False)
def test_local_backup_is_refused_outside_debug(tmp_path: Path) -> None:
    with pytest.raises(CommandError, match="restricted to DEBUG"):
        call_command("backup_local_database", output=str(tmp_path / "backup.dump"))


@pytest.mark.parametrize("output", ["relative.dump", "/path/that/does/not/exist/backup.dump"])
@override_settings(DEBUG=True)
def test_local_backup_rejects_unsafe_destination(output: str) -> None:
    with pytest.raises(CommandError, match="absolute|directory"):
        call_command("backup_local_database", output=output)


@override_settings(DEBUG=True)
def test_local_backup_refuses_paths_inside_application_directory() -> None:
    destination = Path(settings.BASE_DIR) / "arbitrary-name.bin"

    with pytest.raises(CommandError, match="outside the application directory"):
        call_command("backup_local_database", output=str(destination))


@override_settings(DEBUG=True)
def test_local_backup_refuses_to_overwrite(tmp_path: Path) -> None:
    existing = tmp_path / "existing.dump"
    existing.write_bytes(b"keep this file")

    with pytest.raises(CommandError, match="overwrite"):
        call_command("backup_local_database", output=str(existing))

    assert existing.read_bytes() == b"keep this file"


@pytest.mark.parametrize("backup", ["relative.dump", "/missing/blast-ecom.dump"])
@override_settings(DEBUG=True)
def test_local_restore_rejects_missing_or_malformed_backup(backup: str) -> None:
    with pytest.raises(CommandError, match="regular file"):
        call_command("restore_local_database", backup=backup, database_name="blast_ecom_restore")


@pytest.mark.parametrize("database_name", ["bad-name", "Uppercase", "../outside", "a" * 64])
@override_settings(DEBUG=True)
def test_local_restore_rejects_invalid_database_names(tmp_path: Path, database_name: str) -> None:
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"archive")

    with pytest.raises(CommandError, match="valid PostgreSQL identifier"):
        call_command("restore_local_database", backup=str(backup), database_name=database_name)


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_local_restore_refuses_source_database_without_invoking_client(
    tmp_path: Path,
) -> None:
    backup = tmp_path / "valid-looking.dump"
    backup.write_bytes(b"not actually an archive")

    with pytest.raises(CommandError, match="differ from the configured source"):
        call_command(
            "restore_local_database",
            backup=str(backup),
            database_name=settings.DATABASES["default"]["NAME"],
        )


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_local_restore_refuses_existing_target_database(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"archive")
    monkeypatch.setattr(
        "modules.orders.management.commands.restore_local_database.require_pg_tool",
        lambda _: "pg_restore",
    )
    monkeypatch.setattr(
        "modules.orders.management.commands.restore_local_database.run_pg_tool",
        lambda *_args, **_kwargs: None,
    )
    connection = connections["default"]
    with patch.object(connection, "cursor") as cursor_factory:
        cursor_factory.return_value.__enter__.return_value.fetchone.return_value = (1,)
        with pytest.raises(CommandError, match="already exists"):
            call_command(
                "restore_local_database",
                backup=str(backup),
                database_name="existing_target",
            )

    cursor_factory.return_value.__enter__.return_value.execute.assert_called_once_with(
        "SELECT 1 FROM pg_database WHERE datname = %s", ["existing_target"]
    )
