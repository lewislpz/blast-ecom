import uuid
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models

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
