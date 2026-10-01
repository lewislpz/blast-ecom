FROM ghcr.io/astral-sh/uv:0.12.19 AS uv

FROM python:3.13.15-slim-bookworm AS builder
COPY --from=uv /uv /uvx /bin/
WORKDIR /build
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

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
