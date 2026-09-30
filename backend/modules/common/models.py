import uuid
from typing import Any

from django.conf import settings
from django.db import models


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="idempotency_records"
    )
    operation = models.CharField(max_length=64)
    key = models.UUIDField()
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "operation", "key"), name="common_idempotency_scope_unique"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(response_status__isnull=True, response_body__isnull=True)
                    | models.Q(response_status__isnull=False, response_body__isnull=False)
                ),
                name="common_idempotency_response_pair",
            ),
            models.CheckConstraint(
                condition=models.Q(response_status__isnull=True)
                | models.Q(response_status__gte=100, response_status__lte=599),
                name="common_idempotency_status_range",
            ),
        ]
        indexes = [models.Index(fields=("expires_at",), name="common_idempotency_expiry_idx")]


class AuditEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=64)
    target_id = models.UUIDField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValueError("Audit entries are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValueError("Audit entries are append-only.")
