from __future__ import annotations

from typing import cast

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from django.http import HttpRequest

from modules.inventory.models import StockAdjustment, StockItem
from modules.inventory.services import adjust_stock
from modules.users.models import User


def _has_staff_permission(request: HttpRequest, permission: str) -> bool:
    user = request.user
    return bool(
        user.is_active and user.is_staff and not user.is_superuser and user.has_perm(permission)
    )


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("product", "on_hand", "reserved", "available", "updated_at")
    readonly_fields = ("product", "on_hand", "reserved", "updated_at")

    def available(self, obj: StockItem) -> int:
        return obj.available

    def has_module_permission(self, request: HttpRequest) -> bool:
        return self.has_view_permission(request)

    def has_view_permission(self, request: HttpRequest, obj: StockItem | None = None) -> bool:
        return _has_staff_permission(request, "inventory.view_stockitem")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: StockItem | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: StockItem | None = None) -> bool:
        return False


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("created_at", "product", "delta", "actor", "reason")
    list_filter = ("created_at",)
    readonly_fields = ("actor", "created_at")
    fields = ("product", "delta", "reason", "actor", "created_at")
    autocomplete_fields = ("product",)

    def has_module_permission(self, request: HttpRequest) -> bool:
        return self.has_view_permission(request)

    def has_view_permission(self, request: HttpRequest, obj: StockAdjustment | None = None) -> bool:
        return _has_staff_permission(
            request, "inventory.view_stockadjustment"
        ) or self.has_add_permission(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return _has_staff_permission(request, "inventory.adjust_stock")

    def has_change_permission(
        self, request: HttpRequest, obj: StockAdjustment | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: StockAdjustment | None = None
    ) -> bool:
        return False

    def save_model(
        self,
        request: HttpRequest,
        obj: StockAdjustment,
        form: ModelForm[StockAdjustment],
        change: bool,
    ) -> None:
        if change:
            raise PermissionDenied("Stock adjustments are append-only.")
        adjustment = adjust_stock(
            product_id=obj.product_id,
            actor=cast(User, request.user),
            delta=obj.delta,
            reason=obj.reason,
        )
        obj.pk = adjustment.pk
        obj.actor = adjustment.actor
        obj.created_at = adjustment.created_at
