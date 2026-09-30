from __future__ import annotations

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from modules.users.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("route_name", "permission_codename", "needs_group", "method", "form_data"),
    [
        ("admin:auth_group_changelist", "view_group", False, "get", {}),
        ("admin:auth_group_add", "add_group", False, "get", {}),
        ("admin:auth_group_change", "change_group", True, "get", {}),
        ("admin:auth_group_delete", "delete_group", True, "get", {}),
        ("admin:auth_group_add", "add_group", False, "post", {"name": "Escalated"}),
        ("admin:auth_group_delete", "delete_group", True, "post", {"post": "yes"}),
        (
            "admin:auth_group_changelist",
            "delete_group",
            True,
            "post",
            {"action": "delete_selected", "_selected_action": "1", "index": "0"},
        ),
    ],
)
def test_staff_group_permissions_do_not_grant_group_admin_access(
    route_name: str,
    permission_codename: str,
    needs_group: bool,
    method: str,
    form_data: dict[str, str],
) -> None:
    content_type = ContentType.objects.get(app_label="auth", model="group")
    permission = Permission.objects.get(
        content_type=content_type,
        codename=permission_codename,
    )
    operators = Group.objects.create(name="Inventory operators")
    staff = User.objects.create_user("operator@example.test", is_staff=True)
    staff.user_permissions.add(permission)
    if route_name == "admin:auth_group_changelist" and method == "post":
        view_permission = Permission.objects.get(
            content_type=content_type,
            codename="view_group",
        )
        staff.user_permissions.add(view_permission)
    if needs_group:
        staff.groups.add(operators)

    client = Client()
    client.force_login(staff)
    route_args = (
        (operators.pk,) if needs_group and route_name != "admin:auth_group_changelist" else ()
    )
    request_data = dict(form_data)
    if "_selected_action" in request_data:
        request_data["_selected_action"] = str(operators.pk)

    request = getattr(client, method)
    response = request(reverse(route_name, args=route_args), data=request_data)

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_cannot_grant_itself_inventory_permission_through_group_admin() -> None:
    change_group = Permission.objects.get(
        content_type__app_label="auth",
        content_type__model="group",
        codename="change_group",
    )
    adjust_stock = Permission.objects.get(
        content_type__app_label="inventory",
        content_type__model="stockadjustment",
        codename="adjust_stock",
    )
    operators = Group.objects.create(name="Inventory operators")
    operators.permissions.add(change_group)
    staff = User.objects.create_user("operator@example.test", is_staff=True)
    staff.groups.add(operators)
    client = Client()
    client.force_login(staff)

    response = client.post(
        reverse("admin:auth_group_change", args=(operators.pk,)),
        {
            "name": operators.name,
            "permissions": [str(change_group.pk), str(adjust_stock.pk)],
            "_save": "Save",
        },
    )

    assert response.status_code == 403
    operators.refresh_from_db()
    staff = User.objects.get(pk=staff.pk)
    assert not operators.permissions.filter(pk=adjust_stock.pk).exists()
    assert not staff.has_perm("inventory.adjust_stock")


@pytest.mark.django_db
def test_superuser_can_manage_group_permissions_as_break_glass_admin() -> None:
    adjust_stock = Permission.objects.get(
        content_type__app_label="inventory",
        content_type__model="stockadjustment",
        codename="adjust_stock",
    )
    operators = Group.objects.create(name="Inventory operators")
    superuser = User.objects.create_superuser(
        "break-glass@example.test", password="A-long-safe-password-123"
    )
    client = Client()
    client.force_login(superuser)

    response = client.post(
        reverse("admin:auth_group_change", args=(operators.pk,)),
        {
            "name": operators.name,
            "permissions": [str(adjust_stock.pk)],
            "_save": "Save",
        },
    )

    assert response.status_code == 302
    operators.refresh_from_db()
    assert operators.permissions.filter(pk=adjust_stock.pk).exists()
