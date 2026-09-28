# Local Development

Status: The Django/React skeleton and dependency locks exist. The complete local stack is not yet runnable because PostgreSQL/Compose setup has not been added. The current backend migration has not been applied to a database.

## Runtime

- Python 3.13.15, with `uv` available on `PATH`.
- Node.js 24.21.0 and npm 11.19.0 (`frontend/.nvmrc`).
- PostgreSQL 17 will be provided by the planned local Compose configuration. Docker/Compose is not currently installed in the implementation environment.

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

The Python checks and React placeholder test/build have run successfully. Django's migration consistency check currently warns that it cannot connect to `localhost:5432`; it reports no model/migration drift, but that warning means the database history check has not run.

## Planned Full Local Flow

Once the database increment is available: start PostgreSQL, apply migrations explicitly, load fictional seed data, then run Django, Vite and the maintenance command as separate host processes. Vite proxies `/api`, `/admin` and `/static` to Django so the browser uses one origin. Do not have application startup apply migrations or reset the database.

## Data and Safety

Seed commands must be idempotent, local-only and non-destructive. Never use real customer data. A named Compose volume is persistence, not a backup. Deleting a volume or resetting data requires an explicit target and approval; no reset-on-start behavior is allowed.

## Future Operational Boundaries

PostgreSQL unavailable: readiness should fail and mutations should return a safe temporary error. If maintenance is stopped, reservations remain conservatively reserved until the process restarts or expiry maintenance runs. Application containers and hosted operations are outside the current local scaffold.
