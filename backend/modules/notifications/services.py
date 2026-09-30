from modules.notifications.models import NotificationIntent
from modules.orders.models import Order


def create_transition_intent(*, order: Order) -> NotificationIntent:
    """Persist notification intent within the caller's business transaction."""
    return NotificationIntent.objects.create(order=order, transition=order.state)
