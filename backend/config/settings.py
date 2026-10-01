"""Minimal settings for the local Blast Ecom application."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set; see docs/development/local-development.md.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
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
    "django.middleware.security.SecurityMiddleware",
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
AUTH_ATTEMPT_LIMITS = {
    "login": {
        "source": {"limit": 30, "window_seconds": 60},
        "identity_source": {"limit": 5, "window_seconds": 900},
    },
    "admin_login": {
        "source": {"limit": 30, "window_seconds": 60},
        "identity_source": {"limit": 5, "window_seconds": 900},
    },
    "registration": {
        "source": {"limit": 10, "window_seconds": 3600},
        "identity_source": {"limit": 3, "window_seconds": 3600},
    },
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Blast Ecom API",
    "DESCRIPTION": "Local simulated commerce API. Real payments and sales are not supported.",
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
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
