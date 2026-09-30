from django.db import transaction

from modules.common.operations import database_now
from modules.notifications.models import NotificationIntent
from modules.orders.models import Order


def create_transition_intent(*, order: Order) -> NotificationIntent:
    """Persist notification intent within the caller's business transaction."""
    return NotificationIntent.objects.create(order=order, transition=order.state)


@transaction.atomic
def simulate_pending_intents(*, limit: int = 100) -> int:
    """Converge local-only notification intents without connecting to a provider."""
    if not 1 <= limit <= 1000:
        raise ValueError("Notification batch limit must be between 1 and 1000.")
    intents = list(
        NotificationIntent.objects.select_for_update(skip_locked=True)
        .filter(state=NotificationIntent.State.PENDING)
        .order_by("created_at", "id")[:limit]
    )
    if not intents:
        return 0
    processed_at = database_now()
    for intent in intents:
        intent.state = NotificationIntent.State.SIMULATED
        intent.simulated_at = processed_at
    NotificationIntent.objects.bulk_update(intents, ["state", "simulated_at"])
    return len(intents)
