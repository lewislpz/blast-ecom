import uuid
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from modules.users.managers import UserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # type: ignore[assignment]
    email = models.EmailField("email address", unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD: str = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects: UserManager = UserManager()  # type: ignore[assignment, misc]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.email = UserManager.normalize_email(self.email)
        super().save(*args, **kwargs)


class AuthAttemptBucket(models.Model):
    """Pseudonymous fixed-window counter shared by application processes."""

    bucket_key = models.CharField(max_length=64, primary_key=True)
    window_started_at = models.DateTimeField()
    attempts = models.PositiveIntegerField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "users_auth_attempt_bucket"


class AccountEmailOutbox(models.Model):
    class Purpose(models.TextChoices):
        VERIFY_EMAIL = "verify_email", "Verify email"
        RESET_PASSWORD = "reset_password", "Reset password"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account_email_outbox")
    purpose = models.CharField(max_length=24, choices=Purpose.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    dead_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users_account_email_outbox"
        indexes = [
            models.Index(
                fields=["delivered_at", "dead_at", "next_attempt_at"],
                name="users_email_outbox_ready_idx",
            )
        ]
