from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView

from modules.common.exceptions import DomainOperationError
from modules.common.serializers import ProblemDetailSerializer
from modules.users.models import User
from modules.users.recovery import (
    reset_password,
    send_local_password_reset_email,
    send_local_verification_email,
    verify_email_token,
)
from modules.users.serializers import (
    AccountSerializer,
    CsrfTokenSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationResultSerializer,
    LoginRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestedSerializer,
    PasswordResetRequestSerializer,
    RegisterRequestSerializer,
)
from modules.users.throttling import AuthenticationAttemptThrottle

CSRF_HEADER = OpenApiParameter(
    name="X-CSRFToken",
    type=str,
    location="header",
    required=True,
    description="Django CSRF token obtained from /api/v1/auth/csrf/.",
)


def account_payload(user: User) -> dict[str, str | bool]:
    return {
        "id": str(user.pk),
        "email": user.email,
        "email_verified": user.email_verified_at is not None,
    }


@method_decorator(never_cache, name="dispatch")
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfBootstrapView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)

    @extend_schema(responses={200: CsrfTokenSerializer})
    def get(self, request: Request) -> Response:
        return Response({"csrf_token": get_token(request._request)})


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)
    throttle_classes = (AuthenticationAttemptThrottle,)
    throttle_scope = "registration"

    def get_throttles(self) -> list[BaseThrottle]:
        if not settings.DEBUG:
            return []
        return super().get_throttles()

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=RegisterRequestSerializer,
        responses={
            201: AccountSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (409, "application/problem+json"): ProblemDetailSerializer,
            (429, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        if not settings.DEBUG:
            raise DomainOperationError(status_code=404, code="NOT_FOUND")
        serializer = RegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        if User.objects.filter(email=email).exists():
            raise DomainOperationError(status_code=409, code="ACCOUNT_UNAVAILABLE")
        try:
            with transaction.atomic():
                user = User.objects.create_user(email=email, password=password, is_active=True)
        except IntegrityError:
            raise DomainOperationError(status_code=409, code="ACCOUNT_UNAVAILABLE") from None
        send_local_verification_email(user)
        return Response(account_payload(user), status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)
    throttle_classes = (AuthenticationAttemptThrottle,)
    throttle_scope = "password_reset"

    def get_throttles(self) -> list[BaseThrottle]:
        if not settings.DEBUG:
            return []
        return super().get_throttles()

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=PasswordResetRequestSerializer,
        responses={202: PasswordResetRequestedSerializer},
    )
    def post(self, request: Request) -> Response:
        if not settings.DEBUG:
            raise DomainOperationError(status_code=404, code="NOT_FOUND")
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email=serializer.validated_data["email"],
            is_active=True,
            is_staff=False,
            is_superuser=False,
        ).first()
        if user is not None and user.has_usable_password():
            send_local_password_reset_email(user)
        return Response(
            {
                "detail": (
                    "If the account is eligible, password reset instructions were sent "
                    "to the local development email console."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)
    throttle_classes = (AuthenticationAttemptThrottle,)
    throttle_scope = "password_reset_confirm"

    def get_throttles(self) -> list[BaseThrottle]:
        if not settings.DEBUG:
            return []
        return super().get_throttles()

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=PasswordResetConfirmSerializer,
        responses={
            200: PasswordResetRequestedSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        if not settings.DEBUG:
            raise DomainOperationError(status_code=404, code="NOT_FOUND")
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        user = User.objects.filter(
            pk=user_id, is_active=True, is_staff=False, is_superuser=False
        ).first()
        token = serializer.validated_data["token"]
        if user is None or not user.has_usable_password():
            raise DomainOperationError(status_code=400, code="PASSWORD_RESET_INVALID")
        if not default_token_generator.check_token(user, token):
            raise DomainOperationError(status_code=400, code="PASSWORD_RESET_INVALID")
        try:
            validate_password(serializer.validated_data["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        if not reset_password(
            user_id=user_id,
            token=token,
            password=serializer.validated_data["password"],
        ):
            raise DomainOperationError(status_code=400, code="PASSWORD_RESET_INVALID")
        return Response(
            {"detail": "The local demo password has been reset."},
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class EmailVerificationConfirmView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)
    throttle_classes = (AuthenticationAttemptThrottle,)
    throttle_scope = "email_verification"

    def get_throttles(self) -> list[BaseThrottle]:
        if not settings.DEBUG:
            return []
        return super().get_throttles()

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=EmailVerificationConfirmSerializer,
        responses={
            200: EmailVerificationResultSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        if not settings.DEBUG:
            raise DomainOperationError(status_code=404, code="NOT_FOUND")
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not verify_email_token(serializer.validated_data["token"]):
            raise DomainOperationError(status_code=400, code="EMAIL_VERIFICATION_INVALID")
        return Response({"verified": True}, status=status.HTTP_200_OK)


@method_decorator(csrf_protect, name="dispatch")
class EmailVerificationRequestView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (AuthenticationAttemptThrottle,)
    throttle_scope = "email_verification_request"

    def get_throttles(self) -> list[BaseThrottle]:
        if not settings.DEBUG:
            return []
        return super().get_throttles()

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=None,
        responses={202: PasswordResetRequestedSerializer},
    )
    def post(self, request: Request) -> Response:
        if not settings.DEBUG:
            raise DomainOperationError(status_code=404, code="NOT_FOUND")
        user = request.user
        if isinstance(user, User) and not user.is_staff and user.email_verified_at is None:
            send_local_verification_email(user)
        return Response(
            {
                "detail": (
                    "If the account needs verification, instructions were sent "
                    "to the local development email console."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)
    throttle_classes = (AuthenticationAttemptThrottle,)
    throttle_scope = "login"

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=LoginRequestSerializer,
        responses={
            200: AccountSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (429, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        django_request = request._request
        user = authenticate(
            request=django_request,
            email=User.objects.normalize_email(serializer.validated_data["email"]),
            password=serializer.validated_data["password"],
        )
        if user is None or user.is_staff or user.is_superuser:
            raise DomainOperationError(status_code=400, code="AUTH_INVALID")
        login(django_request, user)
        return Response(account_payload(user))


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=None,
        responses={
            204: None,
            (403, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: AccountSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
        }
    )
    def get(self, request: Request) -> Response:
        user = request.user
        if not isinstance(user, User):
            raise DomainOperationError(status_code=403, code="AUTH_REQUIRED")
        return Response(account_payload(user))
