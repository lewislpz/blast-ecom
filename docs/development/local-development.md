# Local Development

Status: The Django API and React customer journey run as separate local host processes against PostgreSQL. The customer browser journey has been verified through the Vite same-origin proxy. A reproducible Compose service and seed/maintenance workflow have not been added yet.

## Runtime

- Python 3.13.15, with `uv` available on `PATH`.
- Node.js 24.21.0 and npm 11.19.0 (`frontend/.nvmrc`).
- PostgreSQL 17 will be provided by the planned local Compose configuration. Docker Desktop and Compose are installed; in the current Codex shell the Docker CLI must be invoked through Docker Desktop's resources path because it is not on `PATH`.

Exact locked application packages and verification status are in [tooling.md](tooling.md).

## Configuration and Secrets

Copy `.env.example` to a local `.env`, replace `DJANGO_SECRET_KEY` with a private random value of at least 50 characters, and keep `.env` untracked. For example, generate a value with `python -c 'import secrets; print(secrets.token_urlsafe(50))'`. The current settings require the key explicitly and default database connection details to the local development database. The example file contains no real credential.

The application settings read process environment variables; they do not parse `.env` themselves. In a shell, export the file's values explicitly (`set -a; source .env; set +a`) before running backend commands. With `DJANGO_DEBUG=true`, settings trust only the default local Vite origins (`http://localhost:5173` and `http://127.0.0.1:5173`) for Django's CSRF Origin check. Configure `DJANGO_CSRF_TRUSTED_ORIGINS` explicitly if local hostnames/ports differ. This development exception is empty by default outside DEBUG; production must use the actual same-origin host or a reviewed explicit origin list.

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

From `frontend/` (with Django available at `127.0.0.1:8000`):

```bash
npm ci
npm run typecheck
npm test
npm run lint
npm run format:check
npm run build
npm run test:e2e
```

Run Django on `127.0.0.1:8000`; Playwright starts Vite automatically for E2E runs. The read-only storefront/accessibility check can run directly with `npm run test:e2e`. The purchase journey creates a uniquely named fictional product, account and orders in the configured database. To enable that data-writing test, verify the database is disposable/local and explicitly set `BLAST_ECOM_E2E_ALLOW_DATA_WRITES=true` before `npm run test:e2e`. These synthetic records are intentionally not deleted automatically. PostgreSQL must be migrated and Chromium installed with `npx playwright install chromium`; reproducible Compose and seed commands are still pending.

## Planned Full Local Flow

Once the database increment is available: start PostgreSQL, apply migrations explicitly, load fictional seed data, then run Django, Vite and the maintenance command as separate host processes. Vite proxies `/api`, `/admin` and `/static` to Django so the browser uses one origin. Do not have application startup apply migrations or reset the database.

## Data and Safety

Seed commands must be idempotent, local-only and non-destructive. Never use real customer data. A named Compose volume is persistence, not a backup. Deleting a volume or resetting data requires an explicit target and approval; no reset-on-start behavior is allowed.

## Future Operational Boundaries

PostgreSQL unavailable: readiness should fail and mutations should return a safe temporary error. If maintenance is stopped, reservations remain conservatively reserved until the process restarts or expiry maintenance runs. Application containers and hosted operations are outside the current local scaffold.
