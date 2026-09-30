from __future__ import annotations

import pytest
from django.conf import settings
from django.contrib.auth import authenticate
from django.test import override_settings
from rest_framework.test import APIClient

from modules.users.models import User


def csrf_token(client: APIClient) -> str:
    response = client.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    assert response["Cache-Control"].find("no-store") >= 0
    token = response.json()["csrf_token"]
    assert isinstance(token, str)
    return token


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_csrf_bootstrap_and_local_registration_are_protected_and_customer_only() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    assert client.cookies[settings.CSRF_COOKIE_NAME]["httponly"] is True

    payload = {"email": "  Customer@Example.Test ", "password": "A-long-safe-password-123"}
    denied = client.post("/api/v1/auth/register/", payload, format="json")
    assert denied.status_code == 403
    assert denied["Content-Type"] == "application/problem+json"
    assert denied.json()["code"] == "CSRF_FAILED"

    response = client.post(
        "/api/v1/auth/register/",
        payload,
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    user = User.objects.get(email="customer@example.test")
    assert response.status_code == 201
    assert response.json() == {"id": str(user.pk), "email": user.email}
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password(payload["password"])


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"],
)
def test_local_vite_origin_can_register_with_bootstrapped_csrf_token() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)

    response = client.post(
        "/api/v1/auth/register/",
        {"email": "vite-customer@example.test", "password": "A-long-safe-password-123"},
        format="json",
        HTTP_ORIGIN="http://127.0.0.1:5173",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 201
    assert response.json()["email"] == "vite-customer@example.test"


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_registration_is_disabled_outside_local_debug_mode() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)

    response = client.post(
        "/api/v1/auth/register/",
        {"email": "customer@example.test", "password": "A-long-safe-password-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert User.objects.count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_inputs_are_strict_and_password_errors_do_not_create_users() -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    short = client.post(
        "/api/v1/auth/register/",
        {"email": "customer@example.test", "password": "short", "is_staff": True},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert short.status_code == 400
    assert short["Content-Type"] == "application/problem+json"
    assert short.json()["field_errors"][0]["field"] in {"password", "is_staff"}
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_login_errors_are_generic_and_staff_cannot_use_customer_login() -> None:
    customer = User.objects.create_user(
        "customer@example.test", password="A-long-safe-password-123"
    )
    staff = User.objects.create_user(
        "staff@example.test", password="A-long-safe-password-123", is_staff=True
    )
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)

    invalid = client.post(
        "/api/v1/auth/login/",
        {"email": "missing@example.test", "password": "wrong-password"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    wrong = client.post(
        "/api/v1/auth/login/",
        {"email": customer.email, "password": "wrong-password"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    staff_response = client.post(
        "/api/v1/auth/login/",
        {"email": staff.email, "password": "A-long-safe-password-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert invalid.status_code == wrong.status_code == staff_response.status_code == 400
    assert invalid.json()["code"] == "AUTH_INVALID"
    assert invalid.json()["detail"] == wrong.json()["detail"] == staff_response.json()["detail"]
    assert "wrong-password" not in str(invalid.json())
    assert authenticate(email=customer.email, password="A-long-safe-password-123") == customer


@pytest.mark.django_db
def test_login_rotates_session_me_is_private_and_logout_revokes_it() -> None:
    user = User.objects.create_user("customer@example.test", password="A-long-safe-password-123")
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    initial_session = client.session
    initial_session["anonymous_state"] = "before-login"
    initial_session.save()
    old_session_key = initial_session.session_key

    logged_in = client.post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": "A-long-safe-password-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert logged_in.status_code == 200
    assert logged_in.json() == {"id": str(user.pk), "email": user.email}
    assert client.cookies[settings.SESSION_COOKIE_NAME].value != old_session_key
    assert client.session.get_expiry_age() <= 12 * 60 * 60
    assert client.get("/api/v1/auth/me/").json() == logged_in.json()
    logout_token = csrf_token(client)

    logged_out = client.post(
        "/api/v1/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=logout_token
    )
    assert logged_out.status_code == 204
    assert client.get("/api/v1/auth/me/").status_code == 403


@pytest.mark.django_db
def test_login_requires_csrf_and_request_ids_ignore_client_values() -> None:
    client = APIClient(enforce_csrf_checks=True)

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "customer@example.test", "password": "wrong-password"},
        format="json",
        HTTP_X_REQUEST_ID="client-controlled-id",
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_FAILED"
    assert response["X-Request-ID"] != "client-controlled-id"


@pytest.mark.django_db
def test_staff_admin_session_uses_one_hour_expiry() -> None:
    staff = User.objects.create_user("staff@example.test", is_staff=True)
    client = APIClient()

    client.force_login(staff)

    assert client.session.get_expiry_age() <= 60 * 60


@pytest.mark.django_db
def test_auth_failures_never_log_password_or_accept_unknown_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    response = client.post(
        "/api/v1/auth/login/",
        {"email": "unknown@example.test", "password": "Secret-Not-To-Log-123", "admin": True},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 400
    assert response.json()["field_errors"][0]["field"] == "admin"
    assert "Secret-Not-To-Log-123" not in caplog.text
