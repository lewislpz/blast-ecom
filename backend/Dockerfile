FROM ghcr.io/astral-sh/uv:0.12.19 AS uv

FROM python:3.13.15-slim-bookworm AS builder
COPY --from=uv /uv /uvx /bin/
WORKDIR /build
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM builder AS production-assets
COPY backend/ /build/backend/
WORKDIR /build/backend
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY="$(/opt/venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
    DJANGO_ALLOWED_HOSTS=static-build.blast-ecom.test \
    DJANGO_CSRF_TRUSTED_ORIGINS=https://shop.blast-ecom.test \
    BLAST_ECOM_FRONTEND_URL=https://shop.blast-ecom.test \
    DJANGO_SECURE_HSTS_SECONDS=3600 \
    DATABASE_SSLMODE=verify-full \
    BLAST_ECOM_PAYMENT_PROVIDER=disabled \
    /opt/venv/bin/python manage.py collectstatic --noinput

FROM python:3.13.15-slim-bookworm AS development
RUN groupadd --system --gid 10001 blast-ecom \
    && useradd --system --uid 10001 --gid blast-ecom --home-dir /nonexistent blast-ecom
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings
WORKDIR /app
COPY --from=builder --chown=blast-ecom:blast-ecom /opt/venv /opt/venv
COPY --chown=blast-ecom:blast-ecom backend/ /app/backend/
WORKDIR /app/backend
USER 10001:10001
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python:3.13.15-slim-bookworm AS production
RUN groupadd --system --gid 10001 blast-ecom \
    && useradd --system --uid 10001 --gid blast-ecom --home-dir /nonexistent blast-ecom
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings
WORKDIR /app/backend
COPY --from=builder --chown=blast-ecom:blast-ecom /opt/venv /opt/venv
COPY --chown=blast-ecom:blast-ecom backend/ /app/backend/
COPY --from=production-assets --chown=blast-ecom:blast-ecom \
    /build/backend/staticfiles /app/backend/staticfiles
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=2", "--access-logfile=-", "--error-logfile=-", "config.wsgi:application"]
