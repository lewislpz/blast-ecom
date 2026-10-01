from __future__ import annotations

from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from modules.common.strict_serializers import StrictSerializer
from modules.users.models import User


class RegisterRequestSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True, min_length=12, max_length=128, trim_whitespace=False
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = User(email=User.objects.normalize_email(attrs["email"]))
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        attrs["email"] = user.email
        return attrs


class LoginRequestSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class AccountSerializer(serializers.Serializer[Any]):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    email_verified = serializers.BooleanField()


class PasswordResetRequestSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value: str) -> str:
        return User.objects.normalize_email(value)


class PasswordResetConfirmSerializer(StrictSerializer):
    user_id = serializers.UUIDField()
    token = serializers.CharField(max_length=256, trim_whitespace=False, write_only=True)
    password = serializers.CharField(
        write_only=True, min_length=12, max_length=128, trim_whitespace=False
    )


class EmailVerificationConfirmSerializer(StrictSerializer):
    token = serializers.CharField(max_length=2048, trim_whitespace=False, write_only=True)


class PasswordResetRequestedSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()


class EmailVerificationResultSerializer(serializers.Serializer[Any]):
    verified = serializers.BooleanField()


class CsrfTokenSerializer(serializers.Serializer[Any]):
    csrf_token = serializers.CharField()
