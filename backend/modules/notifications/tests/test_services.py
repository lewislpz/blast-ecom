from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connections
from django.test import override_settings

from modules.inventory.services import adjust_stock
from modules.notifications.models import NotificationIntent
from modules.notifications.services import (
    NotificationBatchResult,
    create_transition_intent,
    process_pending_intents,
)
from modules.orders.models import Order
from modules.orders.services import create_order
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
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

    batch = process_pending_intents(limit=1)
    assert batch.simulated == 1
    assert batch.failed == 0
    assert NotificationIntent.objects.filter(state=NotificationIntent.State.PENDING).count() == 0
    assert (
        NotificationIntent.objects.filter(
            state=NotificationIntent.State.SIMULATED, simulated_at__isnull=False
        ).count()
        == 1
    )
    assert process_pending_intents(limit=1).simulated == 0


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_notification_failure_is_persisted_and_retried_after_worker_restart() -> None:
    customer = User.objects.create_user("retry@example.test", password="not-a-real-password")
    category = Category.objects.create(slug=f"retry-{uuid4().hex[:8]}", name="Retry")
    product = save_product(
        Product(
            sku=f"RETRY-{uuid4().hex[:8]}",
            category=category,
            title="Fictional retry notification product",
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
    intent = create_transition_intent(order=order)

    with patch(
        "modules.notifications.services._send_local_notification",
        side_effect=[RuntimeError("local console failure"), None],
    ) as send_notification:
        failed = process_pending_intents(limit=1)
        intent.refresh_from_db()
        assert failed.simulated == 0
        assert failed.failed == 1
        assert intent.state == NotificationIntent.State.PENDING
        assert intent.attempt_count == 1
        assert intent.last_error_code == "RuntimeError"
        assert intent.simulated_at is None

        restarted = process_pending_intents(limit=1)
        intent.refresh_from_db()
        assert restarted.simulated == 1
        assert restarted.failed == 0
        assert intent.state == NotificationIntent.State.SIMULATED
        assert intent.attempt_count == 2
        assert intent.last_error_code == ""
        assert intent.simulated_at is not None

        idle = process_pending_intents(limit=1)
        assert idle.simulated == 0
        assert idle.failed == 0
        assert send_notification.call_count == 2

    assert Order.objects.get(pk=order.pk).state == Order.State.AWAITING_PAYMENT


@pytest.mark.django_db(transaction=True)
def test_notification_processing_is_disabled_outside_debug() -> None:
    with override_settings(DEBUG=False), pytest.raises(RuntimeError, match="DEBUG mode"):
        process_pending_intents()


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_concurrent_notification_pass_skips_intent_claimed_by_another_worker() -> None:
    customer = User.objects.create_user("concurrent@example.test", password="not-a-real-password")
    category = Category.objects.create(slug=f"concurrent-{uuid4().hex[:8]}", name="Concurrent")
    product = save_product(
        Product(
            sku=f"CONCURRENT-{uuid4().hex[:8]}",
            category=category,
            title="Fictional concurrent notification product",
            unit_price=Decimal("10.00"),
        )
    )
    adjust_stock(product_id=product.pk, actor=customer, delta=1, reason="Fictional test stock")
    order_result = create_order(
        user=customer,
        idempotency_key=uuid4(),
        items=[{"product_id": str(product.pk), "quantity": 1, "expected_unit_price": "10.00"}],
        address={
            "recipient": "Test Customer",
            "address_line_1": "Fictional Road 1",
            "city": "Madrid",
            "country_code": "ES",
        },
    )
    order = Order.objects.get(pk=order_result.body["id"])
    intent = create_transition_intent(order=order)
    claimed = Event()
    release = Event()

    def hold_claimed_intent(_: NotificationIntent) -> None:
        claimed.set()
        if not release.wait(timeout=5):
            raise TimeoutError("Timed out waiting to release local notification test lock.")

    def process_in_worker() -> NotificationBatchResult:
        connections.close_all()
        try:
            return process_pending_intents(limit=1)
        finally:
            connections.close_all()

    with patch(
        "modules.notifications.services._send_local_notification", side_effect=hold_claimed_intent
    ):
        with ThreadPoolExecutor(max_workers=1) as pool:
            worker = pool.submit(process_in_worker)
            assert claimed.wait(timeout=5)
            concurrent_pass = process_pending_intents(limit=1)
            assert concurrent_pass.simulated == 0
            assert concurrent_pass.failed == 0
            release.set()
            completed = worker.result(timeout=5)

    intent.refresh_from_db()
    assert completed.simulated == 1
    assert completed.failed == 0
    assert intent.attempt_count == 1
    assert intent.state == NotificationIntent.State.SIMULATED
