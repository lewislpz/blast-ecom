from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from modules.common.models import IdempotencyRecord
from modules.common.operations import database_now
from modules.inventory.models import Reservation, StockItem
from modules.inventory.services import adjust_stock
from modules.notifications.models import NotificationIntent
from modules.orders.models import Order
from modules.orders.services import create_order
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_local_maintenance_restarts_and_converges_without_repeating_effects() -> None:
    customer = User.objects.create_user("maintenance@example.test", password="not-a-real-password")
    category = Category.objects.create(slug=f"maintenance-{uuid4().hex[:8]}", name="Maintenance")
    product = save_product(
        Product(
            sku=f"MAINT-{uuid4().hex[:8]}",
            category=category,
            title="Fictional maintenance product",
            unit_price=Decimal("10.00"),
        )
    )
    adjust_stock(product_id=product.pk, actor=customer, delta=1, reason="Fictional test stock")
    result = create_order(
        user=customer,
        idempotency_key=uuid4(),
        items=[
            {
                "product_id": str(product.pk),
                "quantity": 1,
                "expected_unit_price": "10.00",
            }
        ],
        address={
            "recipient": "Test Customer",
            "address_line_1": "Fictional Road 1",
            "address_line_2": "",
            "city": "Madrid",
            "region": "",
            "postal_code": "28000",
            "country_code": "ES",
        },
    )
    order = Order.objects.get(pk=result.body["id"])
    Order.objects.filter(pk=order.pk).update(expires_at=database_now() - timedelta(seconds=1))
    expired_key = uuid4()
    IdempotencyRecord.objects.create(
        user=customer,
        operation="orders.create",
        key=expired_key,
        request_hash="0" * 64,
        response_status=409,
        response_body={"code": "expired"},
        expires_at=database_now() - timedelta(seconds=1),
    )

    call_command("run_local_maintenance", "--once", "--batch-size", "10")

    order.refresh_from_db()
    stock = StockItem.objects.get(product=product)
    reservation = Reservation.objects.get(order=order)
    assert order.state == Order.State.EXPIRED
    assert (stock.on_hand, stock.reserved, stock.available) == (1, 0, 1)
    assert reservation.state == Reservation.State.RELEASED
    assert not IdempotencyRecord.objects.filter(key=expired_key).exists()
    assert (
        NotificationIntent.objects.filter(
            order=order, state=NotificationIntent.State.SIMULATED, simulated_at__isnull=False
        ).count()
        == 1
    )

    call_command("run_local_maintenance", "--once", "--batch-size", "10")

    assert Order.objects.get(pk=order.pk).state == Order.State.EXPIRED
    assert NotificationIntent.objects.filter(order=order).count() == 1
    assert (
        StockItem.objects.get(product=product).on_hand,
        StockItem.objects.get(product=product).reserved,
    ) == (
        1,
        0,
    )


@override_settings(DEBUG=True)
def test_local_maintenance_rejects_invalid_batch_size() -> None:
    with pytest.raises(CommandError, match="between 1 and 1000"):
        call_command("run_local_maintenance", "--once", "--batch-size", "0")
