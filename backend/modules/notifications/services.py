from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F

from modules.common.operations import database_now
from modules.notifications.models import NotificationIntent
from modules.orders.models import Order


def create_transition_intent(*, order: Order) -> NotificationIntent:
    """Persist notification intent within the caller's business transaction."""
    return NotificationIntent.objects.create(order=order, transition=order.state)


@transaction.atomic
def process_pending_intents(*, limit: int = 100) -> NotificationBatchResult:
    """Print bounded local notifications and retain failed work for the next pass."""
    if not settings.DEBUG:
        raise RuntimeError("Local notification processing is available only in DEBUG mode.")
    if not 1 <= limit <= 1000:
        raise ValueError("Notification batch limit must be between 1 and 1000.")
    intents = list(
        NotificationIntent.objects.select_for_update(skip_locked=True)
        .select_related("order__customer")
        .filter(state=NotificationIntent.State.PENDING)
        .order_by(F("last_attempt_at").asc(nulls_first=True), "created_at", "id")[:limit]
    )
    if not intents:
        return NotificationBatchResult(simulated=0, failed=0)
    processed_at = database_now()
    simulated = 0
    failed = 0
    for intent in intents:
        intent.attempt_count += 1
        intent.last_attempt_at = processed_at
        try:
            _send_local_notification(intent)
        except Exception as exc:
            intent.last_error_code = type(exc).__name__[:64]
            failed += 1
        else:
            intent.state = NotificationIntent.State.SIMULATED
            intent.simulated_at = processed_at
            intent.last_error_code = ""
            simulated += 1
    NotificationIntent.objects.bulk_update(
        intents,
        ["attempt_count", "last_attempt_at", "last_error_code", "state", "simulated_at"],
    )
    return NotificationBatchResult(simulated=simulated, failed=failed)


@dataclass(frozen=True)
class NotificationBatchResult:
    simulated: int
    failed: int


def _send_local_notification(intent: NotificationIntent) -> None:
    sent = send_mail(
        subject="Blast Ecom local order update",
        message=(
            f"Your local demo order {intent.order_id} is now {intent.transition}.\n"
            "This is a local simulation. No payment or delivery was made.\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[intent.order.customer.email],
        fail_silently=False,
    )
    if sent != 1:
        raise RuntimeError("The local email backend did not accept the notification.")
