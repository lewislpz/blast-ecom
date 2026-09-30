# Local Development

Status: The Django/React skeleton and dependency locks exist. The custom-user migration has been applied to a temporary PostgreSQL 17.11 container. A reproducible Compose service and complete local workflow have not been added yet.

## Runtime

- Python 3.13.15, with `uv` available on `PATH`.
- Node.js 24.21.0 and npm 11.19.0 (`frontend/.nvmrc`).
- PostgreSQL 17 will be provided by the planned local Compose configuration. Docker Desktop and Compose are installed; in the current Codex shell the Docker CLI must be invoked through Docker Desktop's resources path because it is not on `PATH`.

Exact locked application packages and verification status are in [tooling.md](tooling.md).

## Configuration and Secrets

Copy `.env.example` to a local `.env`, replace `DJANGO_SECRET_KEY` with a private random value of at least 50 characters, and keep `.env` untracked. For example, generate a value with `python -c 'import secrets; print(secrets.token_urlsafe(50))'`. The current settings require the key explicitly and default database connection details to the local development database. The example file contains no real credential.

The application settings read process environment variables; they do not parse `.env` themselves. In a shell, export the file's values explicitly (`set -a; source .env; set +a`) before running backend commands.

## Current Scaffold Checks

From `backend/`:

```bash
uv sync --locked
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run python manage.py check
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run python manage.py makemigrations --check --dry-run
uv run ruff check .
uv run ruff format --check .
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run mypy modules
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run pytest
```

From `frontend/`:

```bash
npm ci
npm run typecheck
npm test
npm run lint
npm run format:check
npm run build
```

The Python checks and React placeholder test/build have run successfully. The custom-user migration was applied to a fresh PostgreSQL 17.11 database; Django's system check, migration drift check and migration-history inspection then passed without a database connectivity warning. This was a disposable validation container without a persistent volume, not the developer Compose setup.

## Planned Full Local Flow

Once the database increment is available: start PostgreSQL, apply migrations explicitly, load fictional seed data, then run Django, Vite and the maintenance command as separate host processes. Vite proxies `/api`, `/admin` and `/static` to Django so the browser uses one origin. Do not have application startup apply migrations or reset the database.

## Data and Safety

Seed commands must be idempotent, local-only and non-destructive. Never use real customer data. A named Compose volume is persistence, not a backup. Deleting a volume or resetting data requires an explicit target and approval; no reset-on-start behavior is allowed.

## Future Operational Boundaries

PostgreSQL unavailable: readiness should fail and mutations should return a safe temporary error. If maintenance is stopped, reservations remain conservatively reserved until the process restarts or expiry maintenance runs. Application containers and hosted operations are outside the current local scaffold.
