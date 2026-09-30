from typing import Any

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpRequest

from modules.users.models import User


@receiver(user_logged_in, dispatch_uid="blast_ecom_session_expiry")
def set_role_session_expiry(
    sender: Any,
    request: HttpRequest | None,
    user: User,
    **kwargs: Any,
) -> None:
    """Apply the accepted short staff and 12-hour customer session lifetimes."""
    if request is None:
        return
    age = 3600 if user.is_staff else 12 * 60 * 60
    request.session.set_expiry(age)
