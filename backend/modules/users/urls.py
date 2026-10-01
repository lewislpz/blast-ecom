from django.urls import path

from modules.users.api import (
    CsrfBootstrapView,
    CurrentUserView,
    EmailVerificationConfirmView,
    EmailVerificationRequestView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)

urlpatterns = [
    path("auth/csrf/", CsrfBootstrapView.as_view(), name="csrf-bootstrap"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "auth/email-verification/",
        EmailVerificationRequestView.as_view(),
        name="email-verification-request",
    ),
    path(
        "auth/email-verification/confirm/",
        EmailVerificationConfirmView.as_view(),
        name="email-verification-confirm",
    ),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
]
