import re
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from modules.common.local_database import (
    require_local_database,
    require_pg_tool,
    run_pg_tool,
    validate_restore_source,
)


class Command(BaseCommand):
    help = "Restore a local custom-format backup into a newly created PostgreSQL database."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--backup", required=True, help="Existing absolute backup file path.")
        parser.add_argument(
            "--database-name", required=True, help="Name for a fresh target database."
        )

    def handle(self, *args: object, **options: Any) -> None:
        del args
        database = require_local_database()
        backup = validate_restore_source(options["backup"])
        target_name = options["database_name"]
        if re.fullmatch(r"[a-z][a-z0-9_]{0,62}", target_name) is None:
            raise CommandError(
                "Target database name must be a valid PostgreSQL identifier of 1–63 characters."
            )
        if target_name == database["name"]:
            raise CommandError("Restore target must differ from the configured source database.")

        pg_restore = require_pg_tool("pg_restore")
        run_pg_tool([pg_restore, "--list", str(backup)], database=database)

        connection = connections["default"]
        previous_autocommit = connection.get_autocommit()
        try:
            connection.set_autocommit(True)
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [target_name])
                if cursor.fetchone() is not None:
                    raise CommandError("Restore target already exists; refusing to modify it.")
                cursor.execute(f"CREATE DATABASE {connection.ops.quote_name(target_name)}")
        finally:
            connection.set_autocommit(previous_autocommit)

        run_pg_tool(
            [
                pg_restore,
                "--no-password",
                "--no-owner",
                "--no-privileges",
                "--exit-on-error",
                "--single-transaction",
                f"--host={database['host']}",
                f"--port={database['port']}",
                f"--username={database['user']}",
                f"--dbname={target_name}",
                str(backup),
            ],
            database=database,
        )
        self.stdout.write(self.style.SUCCESS(f"Backup restored into new database: {target_name}"))
