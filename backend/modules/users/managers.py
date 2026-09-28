from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from modules.users.models import User


class UserManager(BaseUserManager["User"]):
    """Create users with a consistently normalized email address."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        if email is None:
            return ""
        return email.strip().lower()

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> User:
        normalized_email = self.normalize_email(email)
        if not normalized_email:
            raise ValueError("An email address is required.")
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)
