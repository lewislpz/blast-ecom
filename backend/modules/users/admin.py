from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.http import HttpRequest


def _is_break_glass_admin(request: HttpRequest) -> bool:
    user = request.user
    return bool(user.is_active and user.is_staff and user.is_superuser)


class BreakGlassGroupAdmin(GroupAdmin):
    def has_module_permission(self, request: HttpRequest) -> bool:
        return _is_break_glass_admin(request)

    def has_view_permission(self, request: HttpRequest, obj: Group | None = None) -> bool:
        return _is_break_glass_admin(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return _is_break_glass_admin(request)

    def has_change_permission(self, request: HttpRequest, obj: Group | None = None) -> bool:
        return _is_break_glass_admin(request)

    def has_delete_permission(self, request: HttpRequest, obj: Group | None = None) -> bool:
        return _is_break_glass_admin(request)


admin.site.unregister(Group)
admin.site.register(Group, BreakGlassGroupAdmin)
