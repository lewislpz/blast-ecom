from __future__ import annotations

from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

from modules.products.models import Category, Product
from modules.products.services import save_category, save_product


def _has_staff_permission(request: HttpRequest, permission: str) -> bool:
    user = request.user
    return bool(
        user.is_active and user.is_staff and not user.is_superuser and user.has_perm(permission)
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "slug", "active", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")

    def has_module_permission(self, request: HttpRequest) -> bool:
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request: HttpRequest, obj: Category | None = None) -> bool:
        return _has_staff_permission(
            request, "products.view_category"
        ) or self.has_change_permission(request, obj)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return _has_staff_permission(request, "products.add_category")

    def has_change_permission(self, request: HttpRequest, obj: Category | None = None) -> bool:
        return _has_staff_permission(request, "products.change_category")

    def has_delete_permission(self, request: HttpRequest, obj: Category | None = None) -> bool:
        return False

    def save_model(
        self, request: HttpRequest, obj: Category, form: ModelForm[Category], change: bool
    ) -> None:
        save_category(obj)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("sku", "title", "category", "unit_price", "active", "updated_at")
    list_filter = ("active", "category")
    search_fields = ("sku", "title")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("category",)

    def has_module_permission(self, request: HttpRequest) -> bool:
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request: HttpRequest, obj: Product | None = None) -> bool:
        return _has_staff_permission(
            request, "products.view_product"
        ) or self.has_change_permission(request, obj)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return _has_staff_permission(request, "products.add_product")

    def has_change_permission(self, request: HttpRequest, obj: Product | None = None) -> bool:
        return _has_staff_permission(request, "products.change_product")

    def has_delete_permission(self, request: HttpRequest, obj: Product | None = None) -> bool:
        return False

    def save_model(
        self, request: HttpRequest, obj: Product, form: ModelForm[Product], change: bool
    ) -> None:
        save_product(obj)
