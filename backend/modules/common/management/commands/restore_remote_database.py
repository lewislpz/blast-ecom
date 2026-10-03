from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from modules.common.local_database import require_pg_tool, run_pg_tool
from modules.common.remote_backup import (
    configured_database,
    create_new_restore_database,
    download_verified_archive,
    remove_temporary_directory,
    restore_database_config,
    temporary_backup_directory,
    validate_restore_database_target,
)


class Command(BaseCommand):
    help = "Verify and restore one exact remote backup version into a new database."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--backup-id", required=True, help="UUID printed by backup_remote_database."
        )
        parser.add_argument(
            "--version-id",
            required=True,
            help="Exact object version printed by backup_remote_database.",
        )
        parser.add_argument("--database-name", required=True, help="New PostgreSQL database name.")

    def handle(self, *args: object, **options: Any) -> None:
        del args
        if not settings.REMOTE_DATABASE_BACKUP_ENABLED:
            raise CommandError("Remote database restore is disabled by configuration.")
        source = configured_database()
        target_name = str(options["database_name"])
        validate_restore_database_target(target_name, source=source)
        temporary_directory = temporary_backup_directory()
        archive = temporary_directory / "database.dump"
        try:
            receipt = download_verified_archive(
                archive,
                backup_id=str(options["backup_id"]),
                version_id=str(options["version_id"]),
            )
            pg_restore = require_pg_tool("pg_restore")
            run_pg_tool([pg_restore, "--list", str(archive)], database=source)
            create_new_restore_database(target_name, source=source)
            run_pg_tool(
                [
                    pg_restore,
                    "--no-password",
                    "--no-owner",
                    "--no-privileges",
                    "--exit-on-error",
                    "--single-transaction",
                    f"--host={source['host']}",
                    f"--port={source['port']}",
                    f"--username={source['user']}",
                    f"--dbname={target_name}",
                    str(archive),
                ],
                database=restore_database_config(source, target_name=target_name),
            )
        finally:
            remove_temporary_directory(temporary_directory)
        self.stdout.write(
            self.style.SUCCESS(
                f"Verified backup {receipt.backup_id} version {receipt.version_id} "
                f"restored into new database {target_name}."
            )
        )
