from decimal import Decimal
from uuid import uuid4

import pytest

from modules.inventory.services import adjust_stock
from modules.notifications.models import NotificationIntent
from modules.notifications.services import create_transition_intent, simulate_pending_intents
from modules.orders.models import Order
from modules.orders.services import create_order
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User


@pytest.mark.django_db(transaction=True)
def test_notification_intents_are_simulated_once_in_bounded_batches() -> None:
    customer = User.objects.create_user("intent@example.test", password="not-a-real-password")
    category = Category.objects.create(slug=f"intent-{uuid4().hex[:8]}", name="Intent")
    product = save_product(
        Product(
            sku=f"INTENT-{uuid4().hex[:8]}",
            category=category,
            title="Fictional notification product",
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
            "city": "Madrid",
            "country_code": "ES",
        },
    )
    order = Order.objects.get(pk=result.body["id"])
    create_transition_intent(order=order)

    assert simulate_pending_intents(limit=1) == 1
    assert NotificationIntent.objects.filter(state=NotificationIntent.State.PENDING).count() == 0
    assert (
        NotificationIntent.objects.filter(
            state=NotificationIntent.State.SIMULATED, simulated_at__isnull=False
        ).count()
        == 1
    )
    assert simulate_pending_intents(limit=1) == 0
