from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.common.exceptions import DomainOperationError
from modules.common.serializers import ProblemDetailSerializer
from modules.users.models import User
from modules.users.serializers import (
    AccountSerializer,
    CsrfTokenSerializer,
    LoginRequestSerializer,
    RegisterRequestSerializer,
)

CSRF_HEADER = OpenApiParameter(
    name="X-CSRFToken",
    type=str,
    location="header",
    required=True,
    description="Django CSRF token obtained from /api/v1/auth/csrf/.",
)


def account_payload(user: User) -> dict[str, str]:
    return {"id": str(user.pk), "email": user.email}


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

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=RegisterRequestSerializer,
        responses={
            201: AccountSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (409, "application/problem+json"): ProblemDetailSerializer,
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
        return Response(account_payload(user), status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes: tuple[()] = ()
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[CSRF_HEADER],
        request=LoginRequestSerializer,
        responses={
            200: AccountSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
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
