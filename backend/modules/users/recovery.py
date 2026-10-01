from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.functions import Now

from modules.users.models import User

EMAIL_VERIFICATION_SALT = "blast-ecom.email-verification.v1"


def _frontend_link(path: str, fragment: str) -> str:
    base_url = settings.FRONTEND_BASE_URL.rstrip("/")
    return f"{base_url}{path}#{fragment}"


def send_local_verification_email(user: User) -> None:
    token = signing.dumps(
        {"user_id": str(user.pk), "email": user.email},
        salt=EMAIL_VERIFICATION_SALT,
    )
    link = _frontend_link("/verify-email", f"token={token}")
    send_mail(
        subject="Verify your Blast Ecom demo email",
        message=(
            "This link only marks the email address as verified in this local demo. "
            "It does not prove ownership of a real mailbox.\n\n"
            f"Open: {link}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_local_password_reset_email(user: User) -> None:
    token = default_token_generator.make_token(user)
    link = _frontend_link("/reset-password", f"user_id={user.pk}&token={token}")
    send_mail(
        subject="Reset your Blast Ecom demo password",
        message=(
            "A password reset was requested for a local Blast Ecom demo account. "
            "If you did not request this, you can ignore this message.\n\n"
            f"Open: {link}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def verify_email_token(token: str) -> bool:
    try:
        payload = signing.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
            max_age=settings.ACCOUNT_TOKEN_MAX_AGE,
        )
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return False
    if not isinstance(payload, dict):
        return False
    user_id = payload.get("user_id")
    email = payload.get("email")
    if not isinstance(user_id, str) or not isinstance(email, str):
        return False
    try:
        user = User.objects.get(pk=UUID(user_id), email=email, is_active=True)
    except (User.DoesNotExist, ValueError):
        return False
    if user.email_verified_at is not None:
        return False
    return (
        User.objects.filter(pk=user.pk, email=email, email_verified_at__isnull=True).update(
            email_verified_at=Now()
        )
        == 1
    )


@transaction.atomic
def reset_password(*, user_id: UUID, token: str, password: str) -> bool:
    try:
        user = User.objects.select_for_update().get(
            pk=user_id, is_active=True, is_staff=False, is_superuser=False
        )
    except User.DoesNotExist:
        return False
    if not user.has_usable_password() or not default_token_generator.check_token(user, token):
        return False
    user.set_password(password)
    user.save(update_fields=["password"])
    return True
