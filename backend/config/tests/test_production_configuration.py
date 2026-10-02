from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.production import parse_boolean, validate_production_configuration


def valid_configuration() -> dict[str, object]:
    return {
        "SECRET_KEY": "s" * 64,
        "ALLOWED_HOSTS": ["shop.example.com", "api.example.com"],
        "CSRF_TRUSTED_ORIGINS": ["https://shop.example.com"],
        "FRONTEND_BASE_URL": "https://shop.example.com",
        "SECURE_HSTS_SECONDS": 86400,
        "DATABASE_SSLMODE": "verify-full",
        "PAYMENT_PROVIDER": "disabled",
        "PUBLIC_ACCOUNT_FLOWS_ENABLED": True,
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.example.com",
        "EMAIL_PORT": 587,
        "EMAIL_HOST_USER": "blast-ecom@example.com",
        "EMAIL_HOST_PASSWORD": "secret",
        "EMAIL_USE_TLS": True,
        "EMAIL_USE_SSL": False,
        "DEFAULT_FROM_EMAIL": "Blast Ecom <no-reply@example.com>",
    }


def test_production_configuration_accepts_secure_public_account_setup() -> None:
    validate_production_configuration(valid_configuration())


def test_production_configuration_allows_only_explicit_stripe_sandbox_credentials() -> None:
    configuration = valid_configuration()
    configuration.update(
        {
            "PAYMENT_PROVIDER": "stripe_sandbox",
            "STRIPE_SECRET_KEY": "sk_test_not-a-real-secret",
            "STRIPE_WEBHOOK_SECRET": "whsec_not-a-real-secret",
        }
    )
    validate_production_configuration(configuration)

    configuration["STRIPE_SECRET_KEY"] = "sk_live_not-a-real-secret"
    with pytest.raises(ImproperlyConfigured, match="test-mode"):
        validate_production_configuration(configuration)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("SECRET_KEY", "dev-key", "SECRET_KEY"),
        ("ALLOWED_HOSTS", ["*"], "ALLOWED_HOSTS"),
        ("ALLOWED_HOSTS", [".example.com"], "ALLOWED_HOSTS"),
        ("ALLOWED_HOSTS", ["shop.*.example.com"], "ALLOWED_HOSTS"),
        ("CSRF_TRUSTED_ORIGINS", ["http://shop.example.com"], "HTTPS"),
        ("CSRF_TRUSTED_ORIGINS", ["https://*.example.com"], "HTTPS"),
        ("FRONTEND_BASE_URL", "http://shop.example.com", "HTTPS"),
        ("SECURE_HSTS_SECONDS", 0, "HSTS"),
        ("DATABASE_SSLMODE", "require", "verify-full"),
        ("PAYMENT_PROVIDER", "simulator", "DEBUG-only"),
        ("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend", "SMTP"),
        ("EMAIL_HOST_PASSWORD", "", "EMAIL_HOST_PASSWORD"),
        ("EMAIL_USE_TLS", False, "TLS or SSL"),
    ],
)
def test_unsafe_production_configuration_fails_closed(
    key: str, value: object, message: str
) -> None:
    configuration = valid_configuration()
    configuration[key] = value

    with pytest.raises(ImproperlyConfigured, match=message):
        validate_production_configuration(configuration)


@pytest.mark.parametrize("raw", ["yes", "1", "TRUE"])
def test_parse_boolean_accepts_true_spellings(raw: str) -> None:
    assert parse_boolean(raw, name="SETTING", default=False) is True


@pytest.mark.parametrize("raw", ["no", "0", "FALSE"])
def test_parse_boolean_accepts_false_spellings(raw: str) -> None:
    assert parse_boolean(raw, name="SETTING", default=True) is False


def test_parse_boolean_rejects_ambiguous_value() -> None:
    with pytest.raises(ImproperlyConfigured, match="SETTING"):
        parse_boolean("sometimes", name="SETTING", default=False)


def test_django_settings_refuse_unsafe_non_debug_startup() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(backend_root),
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "s" * 64,
        "DJANGO_ALLOWED_HOSTS": "*",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://shop.example.test",
        "BLAST_ECOM_FRONTEND_URL": "https://shop.example.test",
        "DATABASE_SSLMODE": "verify-full",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import config.settings"],
        cwd=backend_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "DJANGO_ALLOWED_HOSTS" in result.stderr
    assert "s" * 32 not in result.stderr


def test_valid_production_environment_loads_secure_settings() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(backend_root),
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "t" * 64,
        "DJANGO_ALLOWED_HOSTS": "shop.example.com,api.example.com",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://shop.example.com",
        "BLAST_ECOM_FRONTEND_URL": "https://shop.example.com",
        "BLAST_ECOM_PUBLIC_ACCOUNT_FLOWS_ENABLED": "true",
        "BLAST_ECOM_TRUSTED_PROXY_CIDRS": "10.0.0.0/8",
        "DATABASE_SSLMODE": "verify-full",
        "DJANGO_EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "DJANGO_EMAIL_HOST": "smtp.example.com",
        "DJANGO_EMAIL_HOST_USER": "blast-ecom@example.com",
        "DJANGO_EMAIL_HOST_PASSWORD": "not-a-real-secret",
        "DJANGO_EMAIL_USE_TLS": "true",
        "DJANGO_DEFAULT_FROM_EMAIL": "Blast Ecom <no-reply@example.com>",
        "BLAST_ECOM_PAYMENT_PROVIDER": "stripe_sandbox",
        "BLAST_ECOM_STRIPE_SECRET_KEY": "sk_test_not-a-real-secret",
        "BLAST_ECOM_STRIPE_WEBHOOK_SECRET": "whsec_not-a-real-secret",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import config.settings as s; assert not s.DEBUG; "
            "assert s.SECURE_SSL_REDIRECT and s.SESSION_COOKIE_SECURE; "
            "assert s.DATABASES['default']['OPTIONS']['sslmode'] == 'verify-full'; "
            "assert s.REQUIRE_VERIFIED_CUSTOMER_EMAIL; "
            "assert s.PAYMENT_PROVIDER == 'stripe_sandbox'",
        ],
        cwd=backend_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_production_configuration_rejects_simulator_provider_at_startup() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(backend_root),
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "u" * 64,
        "DJANGO_ALLOWED_HOSTS": "shop.example.com",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://shop.example.com",
        "BLAST_ECOM_FRONTEND_URL": "https://shop.example.com",
        "DATABASE_SSLMODE": "verify-full",
        "BLAST_ECOM_PAYMENT_PROVIDER": "simulator",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import config.settings"],
        cwd=backend_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "DEBUG=true" in result.stderr
