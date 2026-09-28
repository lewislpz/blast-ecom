# Local Development Design

Status: Planned, not runnable. No Compose file, Dockerfile, env file or application exists.

## Selected Arrangement

Native Django and Vite development processes, PostgreSQL in Docker Compose with a local named volume. A Django maintenance command in a separate terminal/process handles expiry, simulated notification delivery and expired idempotency/session cleanup. It uses the same application and database, not an independently owned service.

Vite proxies /api, /admin and Django admin /static assets to Django. Browser sees a single origin; local plain HTTP cookie exceptions are confined to local settings. Hosted development uses HTTPS and Secure cookies.

Do not automatically run migrations from every process start. The future setup sequence is: resolve locked dependencies, start PostgreSQL, explicitly apply migrations, seed fictional data, start backend/frontend and maintenance. There is no claim that docker compose up alone currently launches the application.

## Configuration Contract

Backend required: secret key, database connection and explicit environment. Separate validated settings for allowed hosts, trusted origins, reservation duration (15 minutes default), maintenance interval (60 seconds), session expiries, reset expiry and simulator mode. Reject unsupported simulator mode outside local/test until a deployment is explicitly designed.

Local .env ignored by Git; .env.example placeholders only. Never commit credentials. Frontend uses relative API URLs; VITE_ settings are public and contain no secrets. No hard-coded admin password; create staff credentials interactively later.

## Seed and Data Safety

Use deterministic fictional categories/products/customers and explicit test-only accounts. Seed commands must be idempotent, local-only and non-destructive by default. No real personal data. Compose volume deletion or database reset requires explicit target/approval; no startup reset.

## Recovery and Limits

PostgreSQL unavailable: readiness fails and mutations return safe temporary errors. Stop maintenance: reservations remain conservatively reserved until restart or an expired-order command; backlog must be visible. Local named volumes are persistence, not backups. Application container packaging and hosted operations wait for a working slice.
