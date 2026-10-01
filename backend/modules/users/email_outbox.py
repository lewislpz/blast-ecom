"""Transactional account-email outbox with bounded, at-least-once SMTP delivery."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.utils import timezone

from modules.users.models import AccountEmailOutbox, User
from modules.users.recovery import send_password_reset_email, send_verification_email

logger = logging.getLogger(__name__)
OutboxPurpose = Literal["verify_email", "reset_password"]
MAX_ATTEMPTS = 8
LEASE_SECONDS = 300


@dataclass(frozen=True)
class DeliveryResult:
    attempted: int
    delivered: int
    retried: int
    dead_lettered: int


def enqueue_account_email(*, user: User, purpose: OutboxPurpose) -> AccountEmailOutbox:
    if purpose not in AccountEmailOutbox.Purpose.values:
        raise ValueError("Unsupported account email purpose.")
    return AccountEmailOutbox.objects.create(user=user, purpose=purpose)


@transaction.atomic
def _claim_batch(*, limit: int) -> list[AccountEmailOutbox]:
    if connection.vendor != "postgresql":
        raise ImproperlyConfigured("Account email outbox processing requires PostgreSQL.")
    now = timezone.now()
    messages = list(
        AccountEmailOutbox.objects.select_for_update(skip_locked=True)
        .select_related("user")
        .filter(
            delivered_at__isnull=True,
            dead_at__isnull=True,
            next_attempt_at__lte=now,
        )
        .order_by("created_at", "id")[:limit]
    )
    for message in messages:
        message.attempts += 1
        message.last_attempt_at = now
        message.next_attempt_at = now + timedelta(seconds=LEASE_SECONDS)
        message.save(update_fields=["attempts", "last_attempt_at", "next_attempt_at"])
    return messages


def _deliver(message: AccountEmailOutbox) -> None:
    if message.purpose == AccountEmailOutbox.Purpose.VERIFY_EMAIL:
        send_verification_email(message.user)
        return
    if message.purpose == AccountEmailOutbox.Purpose.RESET_PASSWORD:
        send_password_reset_email(message.user)
        return
    raise ValueError("Unsupported account email purpose.")


def _finish(message_id: UUID, *, error_code: str | None, attempts: int) -> None:
    now = timezone.now()
    values: dict[str, object]
    if error_code is None:
        values = {"delivered_at": now, "last_error_code": ""}
    elif attempts >= MAX_ATTEMPTS:
        values = {
            "dead_at": now,
            "last_error_code": error_code[:64],
        }
    else:
        delay = min(3600, 30 * (2 ** min(attempts - 1, 7)))
        values = {
            "next_attempt_at": now + timedelta(seconds=delay),
            "last_error_code": error_code[:64],
        }
    AccountEmailOutbox.objects.filter(pk=message_id).update(**values)


def process_account_email_outbox(*, limit: int = 100) -> DeliveryResult:
    if not 1 <= limit <= 1000:
        raise ValueError("Outbox batch size must be between 1 and 1000.")
    if not settings.DEBUG and not settings.PUBLIC_ACCOUNT_FLOWS_ENABLED:
        raise ImproperlyConfigured("Public account email delivery is not enabled.")

    attempted = delivered = retried = dead_lettered = 0
    for _ in range(limit):
        # Lease only the message about to be sent. Pre-leasing a large batch lets
        # later rows expire while earlier SMTP calls are still in flight.
        messages = _claim_batch(limit=1)
        if not messages:
            break
        message = messages[0]
        attempted += 1
        try:
            _deliver(message)
        except Exception as exc:
            error_code = type(exc).__name__
            _finish(message.pk, error_code=error_code, attempts=message.attempts)
            logger.warning(
                "Account email delivery failed.",
                extra={"email_purpose": message.purpose, "error_code": error_code},
            )
            if message.attempts >= MAX_ATTEMPTS:
                dead_lettered += 1
            else:
                retried += 1
        else:
            _finish(message.pk, error_code=None, attempts=message.attempts)
            delivered += 1
    return DeliveryResult(
        attempted=attempted,
        delivered=delivered,
        retried=retried,
        dead_lettered=dead_lettered,
    )
