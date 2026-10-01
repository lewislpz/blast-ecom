from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from smtplib import SMTPException
from threading import Event, Lock
from time import sleep
from typing import cast
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail, signing
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from rest_framework.test import APIClient

from modules.users.email_outbox import process_account_email_outbox
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


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    PUBLIC_ACCOUNT_FLOWS_ENABLED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="https://shop.example.test",
    SECURE_SSL_REDIRECT=False,
)
def test_public_password_reset_queues_email_without_revealing_account() -> None:
    from modules.users.models import AccountEmailOutbox

    user = User.objects.create_user("public-reset@example.test", password="Original-safe-pass-123")
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
        REMOTE_ADDR="198.51.100.31",
    )

    assert existing.status_code == missing.status_code == 202
    assert existing.json() == missing.json()
    assert "local development" not in existing.json()["detail"]
    assert (
        AccountEmailOutbox.objects.filter(
            user=user, purpose=AccountEmailOutbox.Purpose.RESET_PASSWORD
        ).count()
        == 1
    )
    assert mail.outbox == []


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    PUBLIC_ACCOUNT_FLOWS_ENABLED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="https://shop.example.test",
    SECURE_SSL_REDIRECT=False,
)
def test_public_verification_resend_is_generic_and_queues_only_unverified_accounts() -> None:
    from modules.users.models import AccountEmailOutbox

    user = User.objects.create_user(
        "resend-public@example.test", password="A-long-safe-password-123"
    )
    client = APIClient(enforce_csrf_checks=True)
    token = csrf_token(client)
    existing = client.post(
        "/api/v1/auth/email-verification/request/",
        {"email": user.email},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    missing = client.post(
        "/api/v1/auth/email-verification/request/",
        {"email": "missing@example.test"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        REMOTE_ADDR="198.51.100.32",
    )

    assert existing.status_code == missing.status_code == 202
    assert existing.json() == missing.json()
    assert (
        AccountEmailOutbox.objects.filter(
            user=user, purpose=AccountEmailOutbox.Purpose.VERIFY_EMAIL
        ).count()
        == 1
    )
    assert mail.outbox == []


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    PUBLIC_ACCOUNT_FLOWS_ENABLED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="https://shop.example.test",
    SECURE_SSL_REDIRECT=False,
)
def test_account_email_outbox_retries_failure_then_delivers_without_logging_recipient(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from modules.users.models import AccountEmailOutbox

    user = User.objects.create_user("private-recipient@example.test", password=None)
    intent = AccountEmailOutbox.objects.create(
        user=user,
        purpose=AccountEmailOutbox.Purpose.VERIFY_EMAIL,
    )
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "modules.users.email_outbox.send_verification_email",
            lambda _user: (_ for _ in ()).throw(SMTPException("private mail transport detail")),
        )
        failure = process_account_email_outbox(limit=1)

    intent.refresh_from_db()
    assert (failure.attempted, failure.retried, failure.delivered) == (1, 1, 0)
    assert intent.attempts == 1
    assert intent.last_error_code == "SMTPException"
    assert intent.delivered_at is None
    assert "private-recipient@example.test" not in caplog.text
    assert "private mail transport detail" not in caplog.text

    intent.next_attempt_at = intent.created_at
    intent.save(update_fields=["next_attempt_at"])
    success = process_account_email_outbox(limit=1)
    intent.refresh_from_db()
    assert (success.attempted, success.delivered, success.retried) == (1, 1, 0)
    assert intent.attempts == 2
    assert intent.delivered_at is not None
    assert intent.last_error_code == ""


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    PUBLIC_ACCOUNT_FLOWS_ENABLED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="https://shop.example.test",
    SECURE_SSL_REDIRECT=False,
)
def test_account_email_outbox_dead_letters_after_bounded_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from modules.users.email_outbox import MAX_ATTEMPTS
    from modules.users.models import AccountEmailOutbox

    user = User.objects.create_user("dead-letter@example.test", password=None)
    intent = AccountEmailOutbox.objects.create(
        user=user,
        purpose=AccountEmailOutbox.Purpose.VERIFY_EMAIL,
        attempts=MAX_ATTEMPTS - 1,
    )
    monkeypatch.setattr(
        "modules.users.email_outbox.send_verification_email",
        lambda _user: (_ for _ in ()).throw(SMTPException("transport failure")),
    )

    result = process_account_email_outbox(limit=1)
    intent.refresh_from_db()

    assert (result.attempted, result.dead_lettered, result.retried) == (1, 1, 0)
    assert intent.attempts == MAX_ATTEMPTS
    assert intent.dead_at is not None


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=False,
    PUBLIC_ACCOUNT_FLOWS_ENABLED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="https://shop.example.test",
    SECURE_SSL_REDIRECT=False,
)
def test_slow_outbox_batch_does_not_reclaim_later_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from modules.users import email_outbox
    from modules.users.models import AccountEmailOutbox

    intents = [
        AccountEmailOutbox.objects.create(
            user=User.objects.create_user(f"slow-{index}@example.test", password=None),
            purpose=AccountEmailOutbox.Purpose.VERIFY_EMAIL,
        )
        for index in range(5)
    ]
    monkeypatch.setattr(email_outbox, "LEASE_SECONDS", 0.05)
    first_delivery_started = Event()
    delivered_ids: list[str] = []
    delivered_lock = Lock()

    def slow_delivery(message: AccountEmailOutbox) -> None:
        with delivered_lock:
            delivered_ids.append(str(message.pk))
        first_delivery_started.set()
        sleep(0.04)

    monkeypatch.setattr(email_outbox, "_deliver", slow_delivery)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first_worker = pool.submit(process_account_email_outbox, limit=5)
        assert first_delivery_started.wait(timeout=2)
        sleep(0.06)
        second_worker = pool.submit(process_account_email_outbox, limit=5)
        first_result = first_worker.result(timeout=5)
        second_result = second_worker.result(timeout=5)

    assert first_result.attempted + second_result.attempted == len(intents)
    assert len(delivered_ids) == len(intents)
    assert len(set(delivered_ids)) == len(intents)
    assert all(
        attempts == 1 for attempts in AccountEmailOutbox.objects.values_list("attempts", flat=True)
    )
    assert AccountEmailOutbox.objects.filter(delivered_at__isnull=False).count() == len(intents)


def test_account_email_outbox_command_bounds_batch_size_and_reports_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from modules.users.email_outbox import DeliveryResult

    calls: list[int] = []

    def process(*, limit: int) -> DeliveryResult:
        calls.append(limit)
        return DeliveryResult(attempted=2, delivered=1, retried=1, dead_lettered=0)

    monkeypatch.setattr(
        "modules.users.management.commands.process_account_email_outbox.process_account_email_outbox",
        process,
    )
    output = StringIO()
    call_command("process_account_email_outbox", "--batch-size=25", stdout=output)

    assert calls == [25]
    assert output.getvalue() == (
        "account_email_outbox attempted=2 delivered=1 retried=1 dead_lettered=0.\n"
    )
    with pytest.raises(CommandError, match="Batch size"):
        call_command("process_account_email_outbox", "--batch-size=1001")
