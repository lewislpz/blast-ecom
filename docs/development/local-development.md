# Local Development

Status: The Django API, React customer journey and maintenance worker run as separate local host processes. Docker Compose provides PostgreSQL only; the application itself is not containerized. The customer browser journey has been verified through the Vite same-origin proxy.

## Runtime

- Python 3.13.15, with `uv` available on `PATH`.
- Node.js 24.21.0 and npm 11.19.0 (`frontend/.nvmrc`).
- PostgreSQL 17.11 runs through Docker Compose. Docker Desktop and Compose are required.

Exact locked application packages and verification status are in [tooling.md](tooling.md).

## Configuration and Secrets

Copy `.env.example` to a local `.env`, replace `DJANGO_SECRET_KEY` with a private random value of at least 50 characters and set a private `DATABASE_PASSWORD`; keep `.env` untracked. For example, generate values with `python -c 'import secrets; print(secrets.token_urlsafe(50))'`. The example file contains no real credential. Compose binds PostgreSQL to loopback only and requires the password variable; it never publishes credentials in the image or source.

The application settings read process environment variables; they do not parse `.env` themselves. In each backend shell, export the file's values explicitly (`set -a; source .env; set +a`). With `DJANGO_DEBUG=true`, settings trust only the default local Vite origins (`http://localhost:5173` and `http://127.0.0.1:5173`) for Django's CSRF Origin check. Configure `DJANGO_CSRF_TRUSTED_ORIGINS` explicitly if local hostnames/ports differ. This development exception is empty by default outside DEBUG; production must use the actual same-origin host or a reviewed explicit origin list.

## Start the local stack

1. Copy and edit `.env` as described above. Compose automatically reads it from the repository root.
   If port 5432 is already occupied, choose the same free loopback port for both `DATABASE_PORT` and `BLAST_ECOM_POSTGRES_HOST_PORT` (for example, `55432`).
2. Start only PostgreSQL and wait for its connection health check:

   ```bash
   docker compose up -d --wait postgres
   ```

3. In a backend shell, load the variables, install locked dependencies, apply migrations explicitly, and seed the fictional catalog once:

   ```bash
   set -a; source .env; set +a
   cd backend
   uv sync --locked
   uv run python manage.py migrate
   BLAST_ECOM_ALLOW_LOCAL_SEED=true uv run python manage.py seed_local_catalog
   uv run python manage.py check
   uv run python manage.py runserver 127.0.0.1:8000
   ```

   The seed command requires `DEBUG=true`, a loopback database host and the explicit `BLAST_ECOM_ALLOW_LOCAL_SEED=true` opt-in. It creates one fictional product with five units only when that SKU is new. Re-running it never rewrites an existing product or stock level. It creates an inactive, passwordless audit actor for the initial stock adjustment.

4. In another shell, start the frontend:

   ```bash
   cd frontend
   npm ci
   npm run dev -- --host 127.0.0.1
   ```

5. In a third backend shell, run the restartable local maintenance loop:

   ```bash
   set -a; source .env; set +a
   cd backend
   uv run python manage.py run_local_maintenance --interval-seconds 10 --batch-size 100
   ```

   Stop it with Ctrl-C; restart with the same command. Each bounded pass expires due orders and releases their reservations, marks pending notification intents as locally simulated (no email/SMS is sent), and removes expired idempotency records. Run `--once` for a single pass. It never deletes orders, customers, audit entries or notification intents.

The browser is at `http://127.0.0.1:5173`; database readiness is exposed at `http://127.0.0.1:8000/health/ready/`. Readiness checks a live `SELECT 1` connection, not migration state. API operations return a generic 503 Problem Details response when PostgreSQL is unavailable; the response does not expose database errors.

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

Run Django on `127.0.0.1:8000`; Playwright starts Vite automatically for E2E runs. The read-only storefront/accessibility check can run directly with `npm run test:e2e`. The purchase journey creates a uniquely named fictional product, account and orders in the configured database. To enable that data-writing test, verify the database is disposable/local and explicitly set `BLAST_ECOM_E2E_ALLOW_DATA_WRITES=true` before `npm run test:e2e`. These synthetic records are intentionally not deleted automatically. PostgreSQL must be migrated and Chromium installed with `npx playwright install chromium`.

## Data and Safety

The Compose service uses a named volume that survives container recreation and ordinary `docker compose down`. Do not pass `-v` or remove the volume unless intentionally deleting the entire local database after confirming the exact target. There is no reset-on-start behavior. E2E tests also create fictional product/account/order records and deliberately retain them; only set `BLAST_ECOM_E2E_ALLOW_DATA_WRITES=true` after confirming the configured database is local and disposable. Never use real customer data.

## Future Operational Boundaries

Compose's `pg_isready` indicates that PostgreSQL accepts connections; `/health/ready/` verifies application connectivity. Neither check verifies a full purchase transaction. If maintenance is stopped, an expired reservation remains conservatively reserved until the process restarts or expiry maintenance runs. Application containers and hosted operations are outside the current local scaffold.
