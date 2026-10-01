"""Fail-closed production configuration validation."""

from __future__ import annotations

from collections.abc import Mapping
from email.utils import parseaddr
from ipaddress import IPv4Network, IPv6Network, ip_network
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

type Network = IPv4Network | IPv6Network


def parse_boolean(raw: str | None, *, name: str, default: bool) -> bool:
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be an explicit boolean value.")


def parse_trusted_proxy_cidrs(raw: str) -> tuple[str, ...]:
    values = tuple(value.strip() for value in raw.split(",") if value.strip())
    try:
        return tuple(str(ip_network(value, strict=False)) for value in values)
    except ValueError as exc:
        message = "BLAST_ECOM_TRUSTED_PROXY_CIDRS contains an invalid CIDR."
        raise ImproperlyConfigured(message) from exc


def _https_origin(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and bool(parsed.hostname)
        and "*" not in parsed.hostname
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and parsed.path in {"", "/"}
    )


def _setting_int(configuration: Mapping[str, object], key: str, default: int) -> int:
    value = configuration.get(key, default)
    if not isinstance(value, (str, int)):
        raise ImproperlyConfigured(f"Production {key} must be an integer.")
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"Production {key} must be an integer.") from exc


def validate_production_configuration(configuration: Mapping[str, object]) -> None:
    """Reject unsafe settings before a non-debug application can serve traffic."""
    secret = configuration.get("SECRET_KEY")
    if not isinstance(secret, str) or len(secret) < 50 or "replace-this" in secret.lower():
        raise ImproperlyConfigured(
            "Production DJANGO_SECRET_KEY must be private and at least 50 characters."
        )

    hosts = configuration.get("ALLOWED_HOSTS")
    if (
        not isinstance(hosts, (list, tuple))
        or not hosts
        or any(
            not isinstance(host, str)
            or not host
            or "*" in host
            or host.startswith(".")
            or host.lower() in {"localhost", "127.0.0.1", "[::1]"}
            for host in hosts
        )
    ):
        raise ImproperlyConfigured(
            "Production DJANGO_ALLOWED_HOSTS must contain explicit public hosts."
        )

    origins = configuration.get("CSRF_TRUSTED_ORIGINS")
    if (
        not isinstance(origins, (list, tuple))
        or not origins
        or not all(_https_origin(origin) for origin in origins)
    ):
        raise ImproperlyConfigured(
            "Production CSRF_TRUSTED_ORIGINS must be explicit HTTPS origins."
        )

    frontend_url = configuration.get("FRONTEND_BASE_URL")
    if not _https_origin(frontend_url):
        raise ImproperlyConfigured("Production BLAST_ECOM_FRONTEND_URL must be an HTTPS origin.")

    hsts_seconds = _setting_int(configuration, "SECURE_HSTS_SECONDS", 0)
    if hsts_seconds < 3600:
        raise ImproperlyConfigured("Production HSTS must be enabled for at least one hour.")

    if configuration.get("DATABASE_SSLMODE") != "verify-full":
        raise ImproperlyConfigured("Production DATABASE_SSLMODE must be verify-full.")

    if configuration.get("PUBLIC_ACCOUNT_FLOWS_ENABLED"):
        if configuration.get("EMAIL_BACKEND") != "django.core.mail.backends.smtp.EmailBackend":
            raise ImproperlyConfigured(
                "Public accounts require an explicitly configured SMTP backend."
            )
        required_mail_values = (
            "EMAIL_HOST",
            "EMAIL_HOST_USER",
            "EMAIL_HOST_PASSWORD",
        )
        if any(
            not isinstance(configuration.get(name), str) or not configuration[name]
            for name in required_mail_values
        ):
            raise ImproperlyConfigured(
                "Public accounts require EMAIL_HOST, EMAIL_HOST_USER and EMAIL_HOST_PASSWORD."
            )
        port = _setting_int(configuration, "EMAIL_PORT", 0)
        if not 1 <= port <= 65535:
            raise ImproperlyConfigured("EMAIL_PORT must be a valid SMTP port.")
        if bool(configuration.get("EMAIL_USE_TLS")) == bool(configuration.get("EMAIL_USE_SSL")):
            raise ImproperlyConfigured("SMTP must use exactly one of TLS or SSL.")
        from_email = configuration.get("DEFAULT_FROM_EMAIL")
        _, address = parseaddr(from_email if isinstance(from_email, str) else "")
        if "@" not in address or address.rsplit("@", 1)[1].lower() in {"localhost", "example.test"}:
            raise ImproperlyConfigured(
                "Public account email needs a verified non-local sender domain."
            )


def parse_networks(values: tuple[str, ...]) -> tuple[Network, ...]:
    try:
        return tuple(ip_network(value, strict=False) for value in values)
    except ValueError as exc:
        raise ImproperlyConfigured(
            "BLAST_ECOM_TRUSTED_PROXY_CIDRS contains an invalid CIDR."
        ) from exc
