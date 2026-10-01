from __future__ import annotations

from typing import cast
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail, signing
from django.test import override_settings
from rest_framework.test import APIClient

from modules.users.models import User
from modules.users.recovery import EMAIL_VERIFICATION_SALT


def csrf_token(client: APIClient) -> str:
    response = client.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    payload = cast(dict[str, str], response.json())
    return payload["csrf_token"]


def link_payload(message: str) -> dict[str, str]:
    link = next(
        line.removeprefix("Open: ") for line in message.splitlines() if line.startswith("Open: ")
    )
    return {key: value[0] for key, value in parse_qs(urlsplit(link).fragment).items()}


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://127.0.0.1:5173",
)
def test_password_reset_request_is_generic_and_sends_only_to_eligible_account() -> None:
    user = User.objects.create_user("reset@example.test", password="Original-safe-pass-123")
    User.objects.create_user("staff@example.test", password="Staff-safe-pass-123", is_staff=True)
    User.objects.create_user(
        "inactive@example.test", password="Inactive-safe-pass-123", is_active=False
    )
    User.objects.create_user("passwordless@example.test", password=None)
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)

    existing = client.post(
        "/api/v1/auth/password-reset/",
        {"email": user.email},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    missing = client.post(
        "/api/v1/auth/password-reset/",
        {"email": "missing@example.test"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    ineligible = client.post(
        "/api/v1/auth/password-reset/",
        {"email": "staff@example.test"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert existing.status_code == missing.status_code == ineligible.status_code == 202
    assert existing.json() == missing.json() == ineligible.json()
    assert existing.json()["detail"] == (
        "If the account is eligible, password reset instructions were sent "
        "to the local development email console."
    )
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    assert link_payload(cast(str, mail.outbox[0].body))["user_id"] == str(user.pk)
    assert "token=" not in str(existing.json())


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_RESET_TIMEOUT=3600,
    FRONTEND_BASE_URL="http://127.0.0.1:5173",
)
def test_password_reset_is_one_time_validated_and_invalidates_existing_session() -> None:
    user = User.objects.create_user("reset@example.test", password="Original-safe-pass-123")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    token = csrf_token(client)
    requested = client.post(
        "/api/v1/auth/password-reset/",
        {"email": user.email},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    link = link_payload(cast(str, mail.outbox[0].body))
    assert requested.status_code == 202

    changed = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "user_id": link["user_id"],
            "token": link["token"],
            "password": "Replacement-safe-pass-456",
        },
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert changed.status_code == 200
    assert client.get("/api/v1/auth/me/").status_code == 403
    user.refresh_from_db()
    assert user.check_password("Replacement-safe-pass-456")
    assert not user.check_password("Original-safe-pass-123")

    replay = APIClient(enforce_csrf_checks=True)
    replay_token = csrf_token(replay)
    rejected = replay.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "user_id": link["user_id"],
            "token": link["token"],
            "password": "Another-safe-password-789",
        },
        format="json",
        HTTP_X_CSRFTOKEN=replay_token,
    )
    assert rejected.status_code == 400
    assert rejected.json()["code"] == "PASSWORD_RESET_INVALID"
    assert default_token_generator.check_token(user, link["token"]) is False


@pytest.mark.django_db
@override_settings(DEBUG=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_rejects_weak_password_and_invalid_or_missing_tokens() -> None:
    user = User.objects.create_user("reset@example.test", password="Original-safe-pass-123")
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    client.post(
        "/api/v1/auth/password-reset/",
        {"email": user.email},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    link = link_payload(cast(str, mail.outbox[0].body))

    weak = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {**link, "password": "short"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    invalid = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            **link,
            "token": "invalid-token",
            "password": "Replacement-safe-pass-456",
        },
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert weak.status_code == 400
    assert weak.json()["field_errors"][0]["field"] == "password"
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "PASSWORD_RESET_INVALID"
    user.refresh_from_db()
    assert user.check_password("Original-safe-pass-123")


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    AUTH_ATTEMPT_LIMITS={
        "password_reset": {
            "source": {"limit": 10, "window_seconds": 60},
            "identity_source": {"limit": 1, "window_seconds": 3600},
        }
    },
)
def test_password_reset_request_is_throttled_by_normalized_email() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    payload = {"email": "  unknown@example.test "}
    first = client.post(
        "/api/v1/auth/password-reset/",
        payload,
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    second = client.post(
        "/api/v1/auth/password-reset/",
        {"email": "unknown@example.test"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert first.status_code == 202
    assert second.status_code == 429
    assert second["Retry-After"]
    assert second.json()["code"] == "RATE_LIMITED"


@pytest.mark.django_db
@override_settings(DEBUG=True, PASSWORD_RESET_TIMEOUT=-1)
def test_password_reset_rejects_expired_tokens() -> None:
    user = User.objects.create_user("expired@example.test", password="Original-safe-pass-123")
    client = APIClient(enforce_csrf_checks=True)
    csrf = csrf_token(client)
    token = default_token_generator.make_token(user)

    response = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {"user_id": str(user.pk), "token": token, "password": "Replacement-safe-pass-456"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "PASSWORD_RESET_INVALID"
    user.refresh_from_db()
    assert user.check_password("Original-safe-pass-123")


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://127.0.0.1:5173",
)
def test_local_email_verification_marks_account_once_without_gating_login() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    registered = client.post(
        "/api/v1/auth/register/",
        {"email": "verify@example.test", "password": "A-long-safe-password-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    user = User.objects.get(email="verify@example.test")
    assert registered.status_code == 201
    assert registered.json()["email_verified"] is False
    assert len(mail.outbox) == 1
    assert "does not prove ownership" in mail.outbox[0].body
    verification_token = link_payload(cast(str, mail.outbox[0].body))["token"]

    verified = client.post(
        "/api/v1/auth/email-verification/confirm/",
        {"token": verification_token},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    replay = client.post(
        "/api/v1/auth/email-verification/confirm/",
        {"token": verification_token},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    login = client.post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": "A-long-safe-password-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert verified.status_code == 200
    assert verified.json() == {"verified": True}
    assert user.__class__.objects.get(pk=user.pk).email_verified_at is not None
    assert replay.status_code == 400
    assert replay.json()["code"] == "EMAIL_VERIFICATION_INVALID"
    assert login.status_code == 200
    assert login.json()["email_verified"] is True


@pytest.mark.django_db
@override_settings(DEBUG=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_signed_in_user_can_request_a_local_verification_link_again() -> None:
    user = User.objects.create_user("resend@example.test", password="A-long-safe-password-123")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    csrf = csrf_token(client)

    response = client.post(
        "/api/v1/auth/email-verification/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )
    user.email_verified_at = user.date_joined
    user.save(update_fields=["email_verified_at"])
    already_verified = client.post(
        "/api/v1/auth/email-verification/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )

    assert response.status_code == already_verified.status_code == 202
    assert response.json() == already_verified.json()
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@override_settings(DEBUG=True, ACCOUNT_TOKEN_MAX_AGE=-1)
def test_local_email_verification_rejects_expired_signature() -> None:
    user = User.objects.create_user("expired@example.test", password="A-long-safe-password-123")
    token = signing.dumps(
        {"user_id": str(user.pk), "email": user.email},
        salt=EMAIL_VERIFICATION_SALT,
    )
    client = APIClient(enforce_csrf_checks=True)
    csrf = csrf_token(client)

    response = client.post(
        "/api/v1/auth/email-verification/confirm/",
        {"token": token},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "EMAIL_VERIFICATION_INVALID"
    user.refresh_from_db()
    assert user.email_verified_at is None


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_recovery_and_verification_routes_are_disabled_outside_debug() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    paths = (
        ("/api/v1/auth/password-reset/", {"email": "demo@example.test"}),
        (
            "/api/v1/auth/password-reset/confirm/",
            {
                "user_id": "2f01e352-2af8-4f5e-b950-cf555082e71b",
                "token": "token",
                "password": "Replacement-safe-pass-456",
            },
        ),
        ("/api/v1/auth/email-verification/confirm/", {"token": "token"}),
    )
    for path, body in paths:
        response = client.post(
            path,
            body,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"


@pytest.mark.django_db
def test_legacy_local_account_remains_usable_without_verification_timestamp() -> None:
    user = User.objects.create_user("legacy@example.test", password="Original-safe-pass-123")
    assert user.email_verified_at is None
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)

    login = client.post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": "Original-safe-pass-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert login.status_code == 200
    assert login.json()["email_verified"] is False
