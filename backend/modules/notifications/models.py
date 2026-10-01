import uuid

from django.db import models


class NotificationIntent(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        SIMULATED = "simulated", "Simulated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order", on_delete=models.PROTECT, related_name="notification_intents"
    )
    transition = models.CharField(max_length=24)
    state = models.CharField(max_length=12, choices=State.choices, default=State.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    simulated_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("order", "transition"), name="notifications_order_transition_unique"
            )
        ]
        indexes = [models.Index(fields=("state", "created_at"), name="notif_state_created_idx")]
