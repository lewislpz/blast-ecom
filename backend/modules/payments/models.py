import uuid

from django.db import models
from django.db.models import Q


class PaymentAttempt(models.Model):
    class Outcome(models.TextChoices):
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        "orders.Order", on_delete=models.PROTECT, related_name="payment_attempt"
    )
    outcome = models.CharField(max_length=12, choices=Outcome.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    simulator_reference = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gte=0), name="payments_amount_nonnegative"),
            models.CheckConstraint(
                condition=Q(outcome__in=["succeeded", "failed"]),
                name="payments_outcome_valid",
            ),
            models.CheckConstraint(condition=Q(currency="EUR"), name="payments_currency_eur"),
        ]
