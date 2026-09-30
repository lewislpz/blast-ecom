from decimal import Decimal

import pytest
from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.test import Client

from modules.inventory.models import StockAdjustment, StockItem
from modules.inventory.services import StockAdjustmentRejected, adjust_stock
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User


@pytest.fixture
def inventory_records() -> tuple[Product, User]:
    category = Category.objects.create(slug="stock", name="Stock")
    product = save_product(
        Product(
            sku="STOCK-1",
            category=category,
            title="Stock test",
            unit_price=Decimal("5.00"),
        )
    )
    actor = User.objects.create_user("operator@example.test")
    return product, actor


@pytest.mark.django_db
def test_adjust_stock_changes_counter_and_appends_audit_entry(
    inventory_records: tuple[Product, User],
) -> None:
    product, actor = inventory_records

    adjustment = adjust_stock(
        product_id=product.pk,
        actor=actor,
        delta=8,
        reason="Supplier delivery",
    )

    stock_item = StockItem.objects.get(product=product)
    assert stock_item.on_hand == 8
    assert adjustment.delta == 8
    assert adjustment.reason == "Supplier delivery"
    assert adjustment.actor == actor


@pytest.mark.django_db
def test_adjustment_cannot_reduce_on_hand_below_reserved(
    inventory_records: tuple[Product, User],
) -> None:
    product, actor = inventory_records
    stock_item = StockItem.objects.get(product=product)
    stock_item.on_hand = 5
    stock_item.reserved = 3
    stock_item.save(update_fields=["on_hand", "reserved"])

    with pytest.raises(StockAdjustmentRejected):
        adjust_stock(product_id=product.pk, actor=actor, delta=-3, reason="Correction")

    stock_item.refresh_from_db()
    assert stock_item.on_hand == 5
    assert StockAdjustment.objects.filter(product=product).count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("delta", [0, True])
def test_adjustment_rejects_zero_and_boolean_delta(
    inventory_records: tuple[Product, User], delta: int | bool
) -> None:
    product, actor = inventory_records

    with pytest.raises(StockAdjustmentRejected):
        adjust_stock(product_id=product.pk, actor=actor, delta=delta, reason="Invalid")


@pytest.mark.django_db(transaction=True)
def test_database_rejects_invalid_product_price_and_stock_invariants() -> None:
    category = Category.objects.create(slug="constraints", name="Constraints")
    product = Product.objects.create(
        sku="CONSTRAINT-1",
        category=category,
        title="Constraint target",
        unit_price=Decimal("1.00"),
    )
    StockItem.objects.create(product=product)

    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.filter(pk=product.pk).update(unit_price=Decimal("0.00"))

    with pytest.raises(IntegrityError), transaction.atomic():
        StockItem.objects.filter(product=product).update(on_hand=2, reserved=3)


@pytest.mark.django_db
def test_stock_adjustment_records_are_append_only(inventory_records: tuple[Product, User]) -> None:
    product, actor = inventory_records
    adjustment = adjust_stock(product_id=product.pk, actor=actor, delta=2, reason="Initial")

    adjustment.reason = "Changed"
    with pytest.raises(ValueError, match="append-only"):
        adjustment.save()
    with pytest.raises(ValueError, match="append-only"):
        adjustment.delete()


@pytest.mark.django_db
def test_admin_stock_action_requires_permission_and_records_actor(
    inventory_records: tuple[Product, User],
) -> None:
    product, _ = inventory_records
    staff = User.objects.create_user("admin-operator@example.test", is_staff=True)
    client = Client()
    client.force_login(staff)

    denied = client.get("/admin/inventory/stockadjustment/add/")
    assert denied.status_code == 403

    permission = Permission.objects.get(
        content_type__app_label="inventory", codename="adjust_stock"
    )
    staff.user_permissions.add(permission)
    client.force_login(User.objects.get(pk=staff.pk))
    accepted = client.post(
        "/admin/inventory/stockadjustment/add/",
        {"product": str(product.pk), "delta": "4", "reason": "Admin receipt"},
    )

    assert accepted.status_code == 302
    assert StockItem.objects.get(product=product).on_hand == 4
    adjustment = StockAdjustment.objects.get(product=product)
    assert adjustment.actor_id == staff.pk
    assert adjustment.reason == "Admin receipt"
