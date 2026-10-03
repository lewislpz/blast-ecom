"""Minimal settings for the local Blast Ecom application."""

import os
from pathlib import Path

from config.production import (
    parse_boolean,
    parse_trusted_proxy_cidrs,
    validate_production_configuration,
)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = parse_boolean(os.environ.get("DJANGO_DEBUG"), name="DJANGO_DEBUG", default=False)
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set; see docs/development/local-development.md.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else ""
    ).split(",")
    if host.strip()
]

_default_csrf_origins = "http://localhost:5173,http://127.0.0.1:5173" if DEBUG else ""
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", _default_csrf_origins).split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "modules.users.admin_config.BlastEcomAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "modules.common.apps.CommonConfig",
    "modules.users.apps.UsersConfig",
    "modules.products.apps.ProductsConfig",
    "modules.inventory.apps.InventoryConfig",
    "modules.orders.apps.OrdersConfig",
    "modules.payments.apps.PaymentsConfig",
    "modules.notifications.apps.NotificationsConfig",
]

MIDDLEWARE = [
    "modules.common.middleware.RequestIdMiddleware",
    "modules.common.middleware.TrustedProxyHeadersMiddleware",
    "django.middleware.security.SecurityMiddleware",
    *([] if DEBUG else ["whitenoise.middleware.WhiteNoiseMiddleware"]),
    "modules.common.middleware.DatabaseUnavailableMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "modules.common.middleware.ApiRequestSizeLimitMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "blast_ecom"),
        "USER": os.environ.get("DATABASE_USER", "blast_ecom"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_USER_MODEL = "users.User"
CSRF_FAILURE_VIEW = "modules.common.api_errors.csrf_failure"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "modules.common.api_errors.problem_detail_exception_handler",
}
_public_account_flows_enabled = parse_boolean(
    os.environ.get("BLAST_ECOM_PUBLIC_ACCOUNT_FLOWS_ENABLED"),
    name="BLAST_ECOM_PUBLIC_ACCOUNT_FLOWS_ENABLED",
    default=False,
)
PUBLIC_ACCOUNT_FLOWS_ENABLED = _public_account_flows_enabled
REQUIRE_VERIFIED_CUSTOMER_EMAIL = not DEBUG

AUTH_ATTEMPT_LIMITS = {
    "login": {
        "source": {"limit": 30, "window_seconds": 60},
        "identity_source": {"limit": 5, "window_seconds": 900},
        "identity_global": {"limit": 10, "window_seconds": 900},
    },
    "admin_login": {
        "source": {"limit": 30, "window_seconds": 60},
        "identity_source": {"limit": 5, "window_seconds": 900},
        "identity_global": {"limit": 10, "window_seconds": 900},
    },
    "registration": {
        "source": {"limit": 10, "window_seconds": 3600},
        "identity_source": {"limit": 3, "window_seconds": 3600},
        "identity_global": {"limit": 3, "window_seconds": 3600},
    },
    "password_reset": {
        "source": {"limit": 20, "window_seconds": 60},
        "identity_source": {"limit": 3, "window_seconds": 3600},
        "identity_global": {"limit": 5, "window_seconds": 3600},
    },
    "password_reset_confirm": {
        "source": {"limit": 20, "window_seconds": 60},
    },
    "email_verification": {
        "source": {"limit": 20, "window_seconds": 60},
    },
    "email_verification_request": {
        "source": {"limit": 5, "window_seconds": 3600},
        "identity_global": {"limit": 5, "window_seconds": 3600},
    },
}
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.dummy.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DJANGO_DEFAULT_FROM_EMAIL", "blast-ecom-local@localhost" if DEBUG else ""
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587" if not DEBUG else "25"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = parse_boolean(
    os.environ.get("DJANGO_EMAIL_USE_TLS"), name="DJANGO_EMAIL_USE_TLS", default=not DEBUG
)
EMAIL_USE_SSL = parse_boolean(
    os.environ.get("DJANGO_EMAIL_USE_SSL"), name="DJANGO_EMAIL_USE_SSL", default=False
)
EMAIL_TIMEOUT = int(os.environ.get("DJANGO_EMAIL_TIMEOUT", "10"))
FRONTEND_BASE_URL = os.environ.get(
    "BLAST_ECOM_FRONTEND_URL", "http://127.0.0.1:5173" if DEBUG else ""
)
_payment_provider_default = "simulator" if DEBUG else "disabled"
PAYMENT_PROVIDER = (
    os.environ.get("BLAST_ECOM_PAYMENT_PROVIDER", _payment_provider_default).strip().lower()
)
STRIPE_SECRET_KEY = os.environ.get("BLAST_ECOM_STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("BLAST_ECOM_STRIPE_WEBHOOK_SECRET", "")
if PAYMENT_PROVIDER not in {"simulator", "stripe_sandbox", "disabled"}:
    raise RuntimeError("BLAST_ECOM_PAYMENT_PROVIDER must be simulator, stripe_sandbox or disabled.")
if PAYMENT_PROVIDER == "simulator" and not DEBUG:
    raise RuntimeError("The simulated payment provider is available only when DJANGO_DEBUG=true.")
if PAYMENT_PROVIDER == "stripe_sandbox" and (
    not STRIPE_SECRET_KEY.startswith("sk_test_") or not STRIPE_WEBHOOK_SECRET.startswith("whsec_")
):
    raise RuntimeError(
        "Stripe sandbox requires BLAST_ECOM_STRIPE_SECRET_KEY (sk_test_) and "
        "BLAST_ECOM_STRIPE_WEBHOOK_SECRET (whsec_)."
    )
REMOTE_DATABASE_BACKUP_ENABLED = parse_boolean(
    os.environ.get("BLAST_ECOM_REMOTE_BACKUP_ENABLED"),
    name="BLAST_ECOM_REMOTE_BACKUP_ENABLED",
    default=False,
)
BACKUP_S3_BUCKET = os.environ.get("BLAST_ECOM_BACKUP_S3_BUCKET", "")
BACKUP_S3_PREFIX = os.environ.get("BLAST_ECOM_BACKUP_S3_PREFIX", "blast-ecom/postgresql")
BACKUP_S3_REGION = os.environ.get("BLAST_ECOM_BACKUP_S3_REGION", "")
BACKUP_S3_ENDPOINT_URL = os.environ.get("BLAST_ECOM_BACKUP_S3_ENDPOINT_URL", "")
BACKUP_S3_ALLOW_LOCAL_HTTP = DEBUG and parse_boolean(
    os.environ.get("BLAST_ECOM_BACKUP_ALLOW_LOCAL_HTTP"),
    name="BLAST_ECOM_BACKUP_ALLOW_LOCAL_HTTP",
    default=False,
)
BACKUP_RETENTION_DAYS = int(os.environ.get("BLAST_ECOM_BACKUP_RETENTION_DAYS", "35"))
if not 1 <= BACKUP_RETENTION_DAYS <= 3650:
    raise RuntimeError("BLAST_ECOM_BACKUP_RETENTION_DAYS must be between 1 and 3650.")
ACCOUNT_TOKEN_MAX_AGE = 60 * 60
PASSWORD_RESET_TIMEOUT = 60 * 60
SPECTACULAR_SETTINGS = {
    "TITLE": "Blast Ecom API",
    "DESCRIPTION": (
        "Blast Ecom commerce API. Payments are local simulations or Stripe sandbox only."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
TRUSTED_PROXY_CIDRS = parse_trusted_proxy_cidrs(
    os.environ.get("BLAST_ECOM_TRUSTED_PROXY_CIDRS", "")
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if TRUSTED_PROXY_CIDRS else None
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0" if DEBUG else "86400"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
USE_X_FORWARDED_HOST = False
USE_X_FORWARDED_PORT = False
DATABASE_SSLMODE = os.environ.get("DATABASE_SSLMODE", "" if DEBUG else "verify-full")
DATABASE_SSLROOTCERT = os.environ.get("DATABASE_SSLROOTCERT", "")
if DATABASE_SSLMODE:
    database_options = {"sslmode": DATABASE_SSLMODE}
    if DATABASE_SSLROOTCERT:
        database_options["sslrootcert"] = DATABASE_SSLROOTCERT
    DATABASES["default"]["OPTIONS"] = database_options
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    validate_production_configuration(
        {
            "SECRET_KEY": SECRET_KEY,
            "ALLOWED_HOSTS": ALLOWED_HOSTS,
            "CSRF_TRUSTED_ORIGINS": CSRF_TRUSTED_ORIGINS,
            "FRONTEND_BASE_URL": FRONTEND_BASE_URL,
            "SECURE_HSTS_SECONDS": SECURE_HSTS_SECONDS,
            "DATABASE_SSLMODE": DATABASE_SSLMODE,
            "PAYMENT_PROVIDER": PAYMENT_PROVIDER,
            "STRIPE_SECRET_KEY": STRIPE_SECRET_KEY,
            "STRIPE_WEBHOOK_SECRET": STRIPE_WEBHOOK_SECRET,
            "PUBLIC_ACCOUNT_FLOWS_ENABLED": PUBLIC_ACCOUNT_FLOWS_ENABLED,
            "EMAIL_BACKEND": EMAIL_BACKEND,
            "EMAIL_HOST": EMAIL_HOST,
            "EMAIL_PORT": EMAIL_PORT,
            "EMAIL_HOST_USER": EMAIL_HOST_USER,
            "EMAIL_HOST_PASSWORD": EMAIL_HOST_PASSWORD,
            "EMAIL_USE_TLS": EMAIL_USE_TLS,
            "EMAIL_USE_SSL": EMAIL_USE_SSL,
            "DEFAULT_FROM_EMAIL": DEFAULT_FROM_EMAIL,
        }
    )
