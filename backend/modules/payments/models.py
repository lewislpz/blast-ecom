import uuid

from django.db import models
from django.db.models import Q


class PaymentAttempt(models.Model):
    class Outcome(models.TextChoices):
        PENDING = "pending", "Pending"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURING = "capturing", "Capturing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class Provider(models.TextChoices):
        SIMULATOR = "simulator", "Simulator"
        STRIPE = "stripe", "Stripe"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        "orders.Order", on_delete=models.PROTECT, related_name="payment_attempt"
    )
    provider = models.CharField(max_length=12, choices=Provider.choices, default=Provider.SIMULATOR)
    outcome = models.CharField(max_length=12, choices=Outcome.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    simulator_reference = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True)
    provider_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    provider_session_url = models.URLField(max_length=2048, blank=True)
    provider_payment_intent_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gte=0), name="payments_amount_nonnegative"),
            models.CheckConstraint(
                condition=Q(
                    outcome__in=["pending", "authorized", "capturing", "succeeded", "failed"]
                ),
                name="payments_outcome_valid",
            ),
            models.CheckConstraint(condition=Q(currency="EUR"), name="payments_currency_eur"),
            models.CheckConstraint(
                condition=Q(provider__in=["simulator", "stripe"]),
                name="payments_provider_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(provider="simulator", simulator_reference__isnull=False)
                    | Q(provider="stripe", simulator_reference__isnull=True)
                ),
                name="payments_simulator_reference_matches_provider",
            ),
        ]


class ProviderEvent(models.Model):
    class Action(models.TextChoices):
        CAPTURE = "capture", "Capture"
        CANCEL = "cancel", "Cancel"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    payment_intent_id = models.CharField(max_length=255)
    payment_attempt = models.ForeignKey(
        PaymentAttempt, on_delete=models.PROTECT, related_name="provider_events"
    )
    amount = models.PositiveBigIntegerField()
    amount_capturable = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    action = models.CharField(max_length=8, choices=Action.choices, default=Action.CANCEL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("received_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["pending", "processed"]),
                name="payments_provider_event_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(action__in=["capture", "cancel"]),
                name="payments_provider_event_action_valid",
            ),
            models.CheckConstraint(
                condition=Q(currency="eur"), name="payments_provider_event_currency_eur"
            ),
        ]
        indexes = [
            models.Index(fields=("status", "received_at"), name="payments_event_pending_idx")
        ]
