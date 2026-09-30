from django.conf import settings
from django.db import transaction

from modules.orders.models import Order
from modules.payments.models import PaymentAttempt


@transaction.atomic
def create_simulated_attempt(*, order: Order) -> PaymentAttempt:
    """Record a server-selected simulated outcome for the locked order."""
    succeeded = bool(getattr(settings, "BLAST_ECOM_SIMULATED_PAYMENT_SUCCESS", True))
    return PaymentAttempt.objects.create(
        order=order,
        outcome=PaymentAttempt.Outcome.SUCCEEDED if succeeded else PaymentAttempt.Outcome.FAILED,
        amount=order.total,
        currency=order.currency,
    )
