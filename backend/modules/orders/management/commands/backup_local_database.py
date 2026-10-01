import os
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from modules.common.local_database import (
    require_local_database,
    require_pg_tool,
    run_pg_tool,
    validate_backup_source,
)


class Command(BaseCommand):
    help = "Create a new custom-format backup of the configured local development database."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--output", required=True, help="New absolute backup file path.")

    def handle(self, *args: object, **options: Any) -> None:
        del args
        database = require_local_database()
        target = validate_backup_source(options["output"])
        executable = require_pg_tool("pg_dump")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".blast-ecom-backup-", dir=target.parent
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            os.chmod(temporary, 0o600)
            run_pg_tool(
                [
                    executable,
                    "--no-password",
                    "--format=custom",
                    f"--host={database['host']}",
                    f"--port={database['port']}",
                    f"--username={database['user']}",
                    f"--dbname={database['name']}",
                    f"--file={temporary}",
                ],
                database=database,
            )
            try:
                os.link(temporary, target)
            except FileExistsError as exc:
                raise CommandError("Refusing to overwrite an existing backup path.") from exc
        finally:
            temporary.unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(f"Local database backup created: {target}"))
