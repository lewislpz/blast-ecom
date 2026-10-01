# Local Development

Status: Docker Compose runs PostgreSQL, the Django API, the React/Vite development server and the maintenance worker. PostgreSQL data uses a persistent named volume; application source is bind-mounted read-only for local edit/reload. This stack is for local development, not production deployment.

## Prerequisites

- Docker Engine/Desktop and Docker Compose.
- PostgreSQL client utilities compatible with PostgreSQL 17 for local backup/restore commands.
- Python 3.13.15 + `uv`, and Node.js 24.21.0 + npm, only if running checks or application processes directly on the host.

Exact locked application packages and verification status are in [tooling.md](tooling.md).

## Configuration and Secrets

Copy `.env.example` to a local `.env`. Replace `DJANGO_SECRET_KEY` with a private random value of at least 50 characters and set a private `DATABASE_PASSWORD`; keep `.env` untracked. For example, generate values with `python -c 'import secrets; print(secrets.token_urlsafe(50))'`. The example file contains no real credential. Compose binds PostgreSQL and the frontend to loopback only, does not publish the API port, and requires the database password; it never bakes credentials into an image.

Compose loads `.env` automatically and configures the internal database hostname `postgres`. The backend and maintenance worker permit that hostname only with DEBUG plus a Compose-provided local-container opt-in. The catalog seed requires its separate, one-time opt-in. If host port `5432` is occupied, change `BLAST_ECOM_POSTGRES_HOST_PORT` to a free port (for example, `55432`); containers continue using internal port `5432`. For host-run commands such as backup/restore, set `.env`'s `DATABASE_PORT` to that same published port.

With `DJANGO_DEBUG=true`, Django trusts the default local Vite origins (`http://localhost:5173` and `http://127.0.0.1:5173`) for CSRF Origin checks. Configure `DJANGO_CSRF_TRUSTED_ORIGINS` explicitly if local hostnames/ports differ. This development exception is empty by default outside DEBUG; production must use the actual same-origin host or a reviewed explicit origin list.

## Start the Local Stack

1. Copy and edit `.env.example` as `.env`.

2. Start PostgreSQL and wait for its health check:

   ```bash
   docker compose up -d --build --wait postgres
   ```

3. Apply database migrations explicitly before starting the maintenance worker:

   ```bash
   docker compose run --build --rm backend python manage.py migrate
   ```

4. Build and start the API, frontend and maintenance process, then seed the fictional catalog once:

   ```bash
   docker compose up -d --build --wait
   docker compose run --rm -e BLAST_ECOM_ALLOW_LOCAL_SEED=true backend python manage.py seed_local_catalog
   ```

   The seed command requires DEBUG, the Compose-only local database opt-in and `BLAST_ECOM_ALLOW_LOCAL_SEED=true`. It creates one fictional product with five units only when the SKU is new. Re-running it does not rewrite an existing product or stock level. Its audit actor is inactive and has no usable password.

5. Open `http://127.0.0.1:5173` and check the stack with `docker compose ps`. The API readiness endpoint is proxied through `http://127.0.0.1:5173/health/ready/`; Django's port is not exposed on the host. Readiness checks a live `SELECT 1`, not migration state. Application source edits under `frontend/src` and `backend` are reflected by the development containers; dependency or Dockerfile changes require a rebuild.

The backend and frontend run as non-root users. The API is reachable by Vite and the internal Compose network only. PostgreSQL and the Vite port are bound to host loopback. No credentials are built into images.

## Local Account Email and Notifications

Registration, password recovery, demo email verification and notification processing are DEBUG-only. Django uses its console email backend; it sends no real email. Inspect `docker compose logs -f backend` for account recovery/verification links and `docker compose logs -f maintenance` for local order-notification messages. Open account links in the browser. They are for local manual testing and do not establish ownership of an actual mailbox. Recovery request responses are identical for eligible and ineligible accounts, and demo verification does not block sign-in.

The maintenance worker expires due orders and releases reservations, prints pending local notification messages and marks successful intents simulated, then removes expired idempotency and authentication-attempt records. Failed notification intents remain pending and are retried on a later pass. The bounded worker is restartable and does not delete orders, customers, audit entries or notification intents. Console output is a local simulation, not external delivery.

## Local PostgreSQL Backup and Restore

Install PostgreSQL client utilities (`pg_dump` and `pg_restore`) compatible with PostgreSQL 17. Store backup archives outside the repository and Docker build context; build-ignore rules for common archive/backup formats are defense in depth, not a substitute for keeping backup data private. Back up to a new absolute path; the command refuses to replace an existing file and creates it with owner-only permissions:

```bash
cd backend
mkdir -p ~/blast-ecom-backups
uv run python manage.py backup_local_database --output ~/blast-ecom-backups/blast-ecom-$(date +%Y%m%d-%H%M%S).dump
```

The destination directory must already exist. Restore only into a new, explicitly named database; the command rejects the configured source database and any existing destination:

```bash
uv run python manage.py restore_local_database \
  --backup ~/blast-ecom-backups/blast-ecom-YYYYMMDD-HHMMSS.dump \
  --database-name blast_ecom_restore_check
```

The restored database is separate from the application's configured source and is not used by the running app unless you explicitly change `DATABASE_NAME`. A failed transactional restore may leave its newly created database empty; choose a different fresh name for a retry. These local commands do not provide scheduling, retention, off-machine copies, production recovery, or an RPO/RTO guarantee. Use fictional data only.

## Checks and Browser Tests

Backend checks from `backend/`:

```bash
uv sync --locked
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run python manage.py check
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run python manage.py makemigrations --check --dry-run
uv run ruff check .
uv run ruff format --check .
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run mypy modules
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" uv run pytest
```

Frontend checks from `frontend/`:

```bash
npm ci
npm run typecheck
npm test
npm run lint
npm run format:check
npm run build
npm run test:e2e
```

The read-only storefront/accessibility check can run directly with `npm run test:e2e`. The purchase journey creates fictional product, account and order data in the configured database. To enable that data-writing test, verify the database is disposable/local and explicitly set `BLAST_ECOM_E2E_ALLOW_DATA_WRITES=true`. Synthetic records are intentionally not deleted automatically. PostgreSQL must be migrated and Chromium installed with `npx playwright install chromium`.

## Data and Safety

The Compose database uses a named volume that survives container recreation and ordinary `docker compose down`. Never pass `-v` or remove the volume unless intentionally deleting the entire local database after confirming the exact target. There is no reset-on-start behavior. Never use real customer data. Do not treat a local backup on the same machine as disaster recovery.

## Operational Boundaries

Health checks verify process/connection readiness, not a full purchase transaction. If maintenance is stopped, an expired reservation remains conservatively reserved until expiry maintenance runs. The Compose configuration is a development topology, not a production deployment design.
