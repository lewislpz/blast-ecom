"""Safety helpers for explicit local PostgreSQL backup and restore operations."""

import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError


def require_local_database() -> dict[str, str]:
    database = settings.DATABASES["default"]
    host = str(database.get("HOST", ""))
    if not settings.DEBUG or not is_local_database_host(host):
        raise CommandError("Database backup/restore is restricted to DEBUG with a local database.")
    return {
        "host": host or "localhost",
        "port": str(database.get("PORT", "5432")),
        "user": str(database.get("USER", "")),
        "password": str(database.get("PASSWORD", "")),
        "name": str(database["NAME"]),
    }


def is_local_database_host(host: str) -> bool:
    return host in {"", "localhost", "127.0.0.1", "::1"} or (
        host == "postgres" and os.environ.get("BLAST_ECOM_ALLOW_LOCAL_CONTAINER_DATABASE") == "true"
    )


def require_pg_tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise CommandError(f"Required PostgreSQL client tool '{name}' is not installed or on PATH.")
    return executable


def tool_environment(database: dict[str, str]) -> dict[str, str]:
    environment = os.environ.copy()
    if database["password"]:
        environment["PGPASSWORD"] = database["password"]
    return environment


def run_pg_tool(arguments: list[str], *, database: dict[str, str]) -> None:
    try:
        result = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            env=tool_environment(database),
            timeout=3600,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        message = f"PostgreSQL client command could not complete: {type(exc).__name__}."
        raise CommandError(message) from None
    if result.returncode:
        # Tool diagnostics can contain hostnames and paths; avoid echoing arbitrary output.
        raise CommandError(f"PostgreSQL client command failed (exit {result.returncode}).")


def validate_backup_source(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise CommandError("Backup path must be an absolute file path.")
    if path.exists() or path.is_symlink():
        raise CommandError("Refusing to overwrite an existing backup path.")
    if not path.parent.is_dir():
        raise CommandError("Backup directory must already exist.")
    application_root = Path(settings.BASE_DIR).resolve()
    if path.parent.resolve().is_relative_to(application_root):
        raise CommandError("Backup files must be stored outside the application directory.")
    return path


def validate_restore_source(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise CommandError("Backup must be an existing regular file at an absolute path.")
    return path
