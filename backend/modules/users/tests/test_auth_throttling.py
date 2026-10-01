from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.apps import apps
from django.conf import settings
from django.db import OperationalError, connections
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from modules.users.models import User
from modules.users.throttling import _increment_bucket, delete_expired_auth_attempt_buckets


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email",
    ["CUSTOMER@example.test", "customer@example.test", " Customer@Example.Test "],
)
def test_login_limits_attempts_per_normalized_identity_and_source(email: str) -> None:
    client = APIClient()
    client.defaults["REMOTE_ADDR"] = "198.51.100.23"
    override_limits = {
        "login": {
            "source": {"limit": 30, "window_seconds": 60},
            "identity_source": {"limit": 2, "window_seconds": 60},
        },
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=override_limits):
        first = client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "wrong-password"},
            format="json",
        )
        second = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
        )
        blocked = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.8",
        )

    assert first.status_code == second.status_code == 400
    assert blocked.status_code == 429
    assert blocked["Content-Type"] == "application/problem+json"
    assert blocked.json()["code"] == "RATE_LIMITED"
    assert int(blocked["Retry-After"]) > 0
    assert "customer@example.test" not in blocked.content.decode().lower()
    assert "198.51.100.23" not in blocked.content.decode()
    assert User.objects.count() == 0

    attempt_bucket = apps.get_model("users", "AuthAttemptBucket")
    keys = list(attempt_bucket.objects.values_list("bucket_key", flat=True))
    assert keys
    assert all("customer@example.test" not in key for key in keys)
    assert all("198.51.100.23" not in key for key in keys)


@pytest.mark.django_db
def test_login_identity_bucket_isolated_by_source_address() -> None:
    client = APIClient()
    limits = {
        "login": {
            "source": {"limit": 30, "window_seconds": 60},
            "identity_source": {"limit": 1, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        first = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            REMOTE_ADDR="198.51.100.1",
        )
        second_source = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            REMOTE_ADDR="198.51.100.2",
        )

    assert first.status_code == second_source.status_code == 400


@pytest.mark.django_db
def test_login_global_identity_bucket_applies_across_source_addresses() -> None:
    client = APIClient()
    limits = {
        "login": {
            "source": {"limit": 30, "window_seconds": 60},
            "identity_source": {"limit": 30, "window_seconds": 60},
            "identity_global": {"limit": 1, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        first = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            REMOTE_ADDR="198.51.100.1",
        )
        blocked = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            REMOTE_ADDR="198.51.100.2",
        )

    assert first.status_code == 400
    assert blocked.status_code == 429


@pytest.mark.django_db
def test_login_source_limit_applies_across_different_emails() -> None:
    client = APIClient()
    limits = {
        "login": {
            "source": {"limit": 1, "window_seconds": 60},
            "identity_source": {"limit": 10, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        first = client.post(
            "/api/v1/auth/login/",
            {"email": "first@example.test", "password": "wrong-password"},
            format="json",
            REMOTE_ADDR="198.51.100.5",
        )
        blocked = client.post(
            "/api/v1/auth/login/",
            {"email": "second@example.test", "password": "wrong-password"},
            format="json",
            REMOTE_ADDR="198.51.100.5",
        )

    assert first.status_code == 400
    assert blocked.status_code == 429


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_registration_has_a_separate_source_rate_limit() -> None:
    client = APIClient()
    token = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
    limits = {
        "registration": {
            "source": {"limit": 1, "window_seconds": 3600},
            "identity_source": {"limit": 10, "window_seconds": 3600},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        first = client.post(
            "/api/v1/auth/register/",
            {"email": "first@example.test", "password": "A-long-safe-password-123"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        blocked = client.post(
            "/api/v1/auth/register/",
            {"email": "second@example.test", "password": "A-long-safe-password-123"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

    assert first.status_code == 201
    assert blocked.status_code == 429
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_csrf_rejections_do_not_consume_authentication_limit() -> None:
    client = APIClient(enforce_csrf_checks=True)
    limits = {
        "login": {
            "source": {"limit": 1, "window_seconds": 60},
            "identity_source": {"limit": 1, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        rejected_one = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
        )
        rejected_two = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
        )
        token = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
        valid_csrf = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

    assert rejected_one.status_code == rejected_two.status_code == 403
    assert valid_csrf.status_code == 400
    assert valid_csrf.json()["code"] == "AUTH_INVALID"


@pytest.mark.django_db
def test_auth_throttle_fails_closed_on_database_outage() -> None:
    client = APIClient()
    with patch(
        "modules.users.throttling._increment_bucket",
        side_effect=OperationalError("private database detail"),
    ):
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
        )

    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "private database detail" not in response.content.decode()


@pytest.mark.django_db
def test_admin_auth_throttle_fails_closed_on_database_outage() -> None:
    client = Client(raise_request_exception=False)
    with patch(
        "modules.users.admin_site.consume_auth_attempts",
        side_effect=OperationalError("private database detail"),
    ):
        response = client.post(
            reverse("admin:login"),
            {"username": "staff@example.test", "password": "wrong-password"},
        )

    assert response.status_code == 503
    assert "private database detail" not in response.content.decode()
    assert "wrong-password" not in response.content.decode()


@pytest.mark.django_db
def test_malformed_login_body_still_consumes_source_limit() -> None:
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
    limits = {
        "login": {
            "source": {"limit": 1, "window_seconds": 60},
            "identity_source": {"limit": 10, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        malformed = client.generic(
            "POST",
            "/api/v1/auth/login/",
            data="{malformed",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        subsequent_valid_shape = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    assert malformed.status_code == 400
    assert subsequent_valid_shape.status_code == 429


@pytest.mark.django_db
def test_staff_admin_login_is_throttled_without_disclosing_identity() -> None:
    User.objects.create_user(
        "staff@example.test", password="A-long-safe-password-123", is_staff=True
    )
    client = Client()
    limits = {
        "admin_login": {
            "source": {"limit": 10, "window_seconds": 60},
            "identity_source": {"limit": 1, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        first = client.post(
            reverse("admin:login"),
            {"username": "staff@example.test", "password": "wrong-password"},
        )
        blocked = client.post(
            reverse("admin:login"),
            {"username": "staff@example.test", "password": "wrong-password"},
        )

    assert first.status_code == 200
    assert blocked.status_code == 429
    assert int(blocked["Retry-After"]) > 0
    assert "staff@example.test" not in blocked.content.decode()
    assert "wrong-password" not in blocked.content.decode()


@pytest.mark.django_db
def test_admin_csrf_rejection_does_not_consume_authentication_limit() -> None:
    client = Client(enforce_csrf_checks=True)
    limits = {
        "admin_login": {
            "source": {"limit": 1, "window_seconds": 60},
            "identity_source": {"limit": 1, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        rejected_one = client.post(
            reverse("admin:login"),
            {"username": "staff@example.test", "password": "wrong-password"},
        )
        rejected_two = client.post(
            reverse("admin:login"),
            {"username": "staff@example.test", "password": "wrong-password"},
        )
        login_page = client.get(reverse("admin:login"))
        csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
        valid_csrf = client.post(
            reverse("admin:login"),
            {
                "username": "staff@example.test",
                "password": "wrong-password",
                "csrfmiddlewaretoken": csrf_token,
            },
            HTTP_REFERER="http://testserver/admin/login/",
        )

    assert rejected_one.status_code == rejected_two.status_code == 403
    assert login_page.status_code == 200
    assert valid_csrf.status_code == 200


@pytest.mark.django_db
def test_superuser_can_log_in_to_admin_with_correct_credentials() -> None:
    User.objects.create_superuser("break-glass@example.test", password="A-long-safe-password-123")
    client = Client()

    response = client.post(
        reverse("admin:login"),
        {
            "username": "break-glass@example.test",
            "password": "A-long-safe-password-123",
            "next": reverse("admin:index"),
        },
    )

    assert response.status_code == 302
    assert response["Location"].endswith(reverse("admin:index"))


@pytest.mark.django_db(transaction=True)
def test_postgres_attempt_increment_is_atomic_under_concurrency() -> None:
    key = uuid4().hex * 2

    def attempt() -> int:
        connections.close_all()
        try:
            return _increment_bucket(key=key, window_seconds=60, limit=10)[0]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=8) as pool:
        attempts = sorted(pool.map(lambda _: attempt(), range(8)))

    assert attempts == list(range(1, 9))


@pytest.mark.django_db(transaction=True)
def test_attempt_counter_is_capped_at_first_denied_attempt() -> None:
    key = uuid4().hex * 2

    attempts = [_increment_bucket(key=key, window_seconds=60, limit=2)[0] for _ in range(5)]

    assert attempts == [1, 2, 3, 3, 3]


@pytest.mark.django_db
def test_expired_auth_buckets_are_removed_in_bounded_batches() -> None:
    bucket_model = apps.get_model("users", "AuthAttemptBucket")
    now = timezone.now()
    expired = [
        bucket_model.objects.create(
            bucket_key=uuid4().hex * 2,
            window_started_at=now - timedelta(minutes=2),
            attempts=1,
            expires_at=now - timedelta(minutes=1),
        )
        for _ in range(3)
    ]

    assert delete_expired_auth_attempt_buckets(limit=2) == 2
    assert bucket_model.objects.filter(pk__in=[bucket.pk for bucket in expired]).count() == 1


@pytest.mark.django_db
def test_auth_attempt_bucket_window_resets_after_expiry() -> None:
    client = APIClient()
    limits = {
        "login": {
            "source": {"limit": 30, "window_seconds": 60},
            "identity_source": {"limit": 1, "window_seconds": 60},
        }
    }

    with override_settings(AUTH_ATTEMPT_LIMITS=limits):
        first = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
        )
        attempt_bucket = apps.get_model("users", "AuthAttemptBucket")
        attempt_bucket.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        after_expiry = client.post(
            "/api/v1/auth/login/",
            {"email": "customer@example.test", "password": "wrong-password"},
            format="json",
        )

    assert first.status_code == after_expiry.status_code == 400
