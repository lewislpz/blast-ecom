import pytest
from django.db import models

from modules.users.managers import UserManager
from modules.users.models import User


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("  Customer@Example.COM ", "customer@example.com"),
        ("sales+demo@EXAMPLE.ORG", "sales+demo@example.org"),
    ],
)
def test_normalize_email(email: str, expected: str) -> None:
    assert UserManager.normalize_email(email) == expected


def test_user_identity_uses_uuid_and_unique_email() -> None:
    assert isinstance(User._meta.pk, models.UUIDField)
    assert User._meta.get_field("email").unique is True
