from uuid import UUID

from modules.payments.models import PaymentAttempt


def get_payment_attempt(*, order_id: UUID) -> PaymentAttempt | None:
    return PaymentAttempt.objects.filter(order_id=order_id).first()
