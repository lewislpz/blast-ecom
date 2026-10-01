from __future__ import annotations

from typing import Any

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from modules.users.throttling import (
    consume_auth_attempts,
    normalize_client_source,
    normalize_identity,
)


class BlastEcomAdminSite(AdminSite):
    @method_decorator(never_cache)
    @method_decorator(login_not_required)
    @method_decorator(csrf_protect)
    def login(
        self, request: HttpRequest, extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        if request.method == "POST" and not request.user.is_authenticated:
            allowed, retry_after = consume_auth_attempts(
                scope="admin_login",
                source=normalize_client_source(request.META.get("REMOTE_ADDR")),
                identity=normalize_identity(request.POST.get("username")),
            )
            if not allowed:
                response = HttpResponse("Too many login attempts. Try again later.", status=429)
                response["Retry-After"] = str(max(1, retry_after))
                return response

        return super().login(request, extra_context)
