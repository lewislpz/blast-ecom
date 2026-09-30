from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from uuid import UUID, uuid1, uuid4

import pytest
from django.db import IntegrityError, connection, connections, transaction
from django.test import override_settings

from modules.common.models import AuditEntry, IdempotencyRecord
from modules.common.operations import OperationResult, database_now
from modules.inventory.models import Reservation, StockItem
from modules.inventory.services import adjust_stock
from modules.notifications.models import NotificationIntent
from modules.orders.models import Order, OrderItem
from modules.orders.services import (
    CheckoutInputError,
    cancel_order,
    create_order,
    simulate_payment,
)
from modules.payments.models import PaymentAttempt
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User

ADDRESS = {
    "recipient": "Ada Example",
    "address_line_1": "1 Fictional Street",
    "address_line_2": "",
    "city": "Madrid",
    "region": "Madrid",
    "postal_code": "28001",
    "country_code": "ES",
}


@pytest.fixture
def shop() -> tuple[User, Product]:
    user = User.objects.create_user("customer@example.test", password="not-a-real-password")
    category = Category.objects.create(slug=f"demo-{uuid4().hex[:8]}", name="Demo")
    product = save_product(
        Product(
            sku=f"DEMO-{uuid4().hex[:8]}",
            category=category,
            title="Fictional product",
            unit_price=Decimal("12.50"),
        )
    )
    adjust_stock(product_id=product.pk, actor=user, delta=2, reason="Fictional opening stock")
    return user, product


def checkout(
    user: User, product: Product, key: UUID | None = None, quantity: int = 1
) -> OperationResult:
    return create_order(
        user=user,
        idempotency_key=key or uuid4(),
        items=[
            {
                "product_id": str(product.pk),
                "quantity": quantity,
                "expected_unit_price": "12.50",
            }
        ],
        address=ADDRESS,
    )


@pytest.mark.django_db(transaction=True)
def test_checkout_snapshots_price_address_and_reserves_stock(shop: tuple[User, Product]) -> None:
    user, product = shop

    result = checkout(user, product)

    assert result.status == 201
    order = Order.objects.get(pk=result.body["id"])
    item = OrderItem.objects.get(order=order)
    stock = StockItem.objects.get(product=product)
    assert order.customer == user
    assert (order.subtotal, order.shipping_total, order.total) == (
        Decimal("12.50"),
        Decimal("0.00"),
        Decimal("12.50"),
    )
    assert order.address_line_1 == ADDRESS["address_line_1"]
    assert (item.sku_snapshot, item.title_snapshot, item.unit_price) == (
        product.sku,
        product.title,
        Decimal("12.50"),
    )
    assert (stock.on_hand, stock.reserved, stock.available) == (2, 1, 1)
    assert Reservation.objects.get(order=order).state == Reservation.State.ACTIVE


@pytest.mark.django_db(transaction=True)
def test_checkout_idempotency_replays_same_order_and_rejects_changed_payload(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    key = uuid4()

    first = checkout(user, product, key)
    replay = checkout(user, product, key)
    changed = create_order(
        user=user,
        idempotency_key=key,
        items=[{"product_id": str(product.pk), "quantity": 2, "expected_unit_price": "12.50"}],
        address=ADDRESS,
    )

    assert first.status == replay.status == 201
    assert replay.replayed is True
    assert first.body == replay.body
    assert changed.status == 409
    assert changed.body["code"] == "IDEMPOTENCY_CONFLICT"
    assert Order.objects.count() == 1
    assert StockItem.objects.get(product=product).reserved == 1


@pytest.mark.django_db(transaction=True)
def test_idempotency_scope_isolated_between_customers(shop: tuple[User, Product]) -> None:
    user, product = shop
    other = User.objects.create_user("other-customer@example.test")
    key = uuid4()

    first = checkout(user, product, key)
    second = checkout(other, product, key)

    assert first.status == second.status == 201
    assert first.body["id"] != second.body["id"]
    assert Order.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_non_v4_idempotency_key_is_rejected_without_side_effects(
    shop: tuple[User, Product],
) -> None:
    user, product = shop

    result = checkout(user, product, key=uuid1())

    assert result.status == 400
    assert result.body["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert IdempotencyRecord.objects.count() == 0
    assert Order.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_checkout_conflicts_are_cached_and_invalid_input_is_not(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    key = uuid4()
    product.unit_price = Decimal("13.00")
    product.save(update_fields=["unit_price", "updated_at"])

    conflict = checkout(user, product, key)
    replay = checkout(user, product, key)
    assert conflict.status == replay.status == 409
    assert replay.replayed is True
    assert conflict.body == replay.body
    with pytest.raises(CheckoutInputError):
        create_order(
            user=user,
            idempotency_key=uuid4(),
            items=[
                {"product_id": str(product.pk), "quantity": True, "expected_unit_price": "13.00"}
            ],
            address=ADDRESS,
        )
    assert IdempotencyRecord.objects.count() == 1
    assert Order.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_checkout_rejects_authoritative_or_unknown_client_fields(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    with pytest.raises(CheckoutInputError):
        create_order(
            user=user,
            idempotency_key=uuid4(),
            items=[
                {
                    "product_id": str(product.pk),
                    "quantity": 1,
                    "expected_unit_price": "12.50",
                    "total": "0.01",
                }
            ],
            address=ADDRESS,
        )
    with pytest.raises(CheckoutInputError):
        create_order(
            user=user,
            idempotency_key=uuid4(),
            items=[{"product_id": str(product.pk), "quantity": 1, "expected_unit_price": "12.50"}],
            address={**ADDRESS, "is_admin": True},
        )
    assert IdempotencyRecord.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_checkout_rejects_product_in_inactive_category(shop: tuple[User, Product]) -> None:
    user, product = shop
    product.category.active = False
    product.category.save(update_fields=["active", "updated_at"])

    result = checkout(user, product)

    assert result.status == 409
    assert result.body["code"] == "PRODUCT_UNAVAILABLE"
    assert Order.objects.count() == 0
    assert StockItem.objects.get(product=product).reserved == 0


@pytest.mark.django_db(transaction=True)
def test_payment_success_consumes_stock_and_creates_one_durable_intent(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    created = checkout(user, product)
    order_id = created.body["id"]

    result = simulate_payment(
        user=user, order_id=Order.objects.get(pk=order_id).pk, idempotency_key=uuid4()
    )

    order = Order.objects.get(pk=order_id)
    stock = StockItem.objects.get(product=product)
    assert result.status == 200
    assert order.state == Order.State.CONFIRMED
    assert (stock.on_hand, stock.reserved) == (1, 0)
    assert Reservation.objects.get(order=order).state == Reservation.State.CONSUMED
    assert PaymentAttempt.objects.get(order=order).outcome == PaymentAttempt.Outcome.SUCCEEDED
    assert NotificationIntent.objects.filter(order=order, transition="confirmed").count() == 1
    assert AuditEntry.objects.filter(target_id=order.pk).count() == 2


@pytest.mark.django_db(transaction=True)
def test_order_and_payment_keep_product_snapshot_after_catalog_change(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk
    product.unit_price = Decimal("19.99")
    product.title = "Renamed later"
    product.save(update_fields=["unit_price", "title", "updated_at"])

    result = simulate_payment(user=user, order_id=order_id, idempotency_key=uuid4())

    item = OrderItem.objects.get(order_id=order_id)
    attempt = PaymentAttempt.objects.get(order_id=order_id)
    assert result.status == 200
    assert (item.title_snapshot, item.unit_price, attempt.amount) == (
        "Fictional product",
        Decimal("12.50"),
        Decimal("12.50"),
    )


@pytest.mark.django_db(transaction=True)
@override_settings(BLAST_ECOM_SIMULATED_PAYMENT_SUCCESS=False)
def test_failed_payment_releases_stock_and_replays_with_new_key(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk

    first = simulate_payment(user=user, order_id=order_id, idempotency_key=uuid4())
    second = simulate_payment(user=user, order_id=order_id, idempotency_key=uuid4())

    stock = StockItem.objects.get(product=product)
    assert first.status == second.status == 200
    assert first.body == second.body
    assert (stock.on_hand, stock.reserved, stock.available) == (2, 0, 2)
    assert PaymentAttempt.objects.filter(order_id=order_id).count() == 1
    assert Reservation.objects.get(order_id=order_id).state == Reservation.State.RELEASED


@pytest.mark.django_db(transaction=True)
def test_cancellation_releases_once_and_is_owner_scoped(shop: tuple[User, Product]) -> None:
    user, product = shop
    other = User.objects.create_user("other@example.test")
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk

    hidden = cancel_order(user=other, order_id=order_id, idempotency_key=uuid4())
    cancelled = cancel_order(user=user, order_id=order_id, idempotency_key=uuid4())
    repeated = cancel_order(user=user, order_id=order_id, idempotency_key=uuid4())

    stock = StockItem.objects.get(product=product)
    assert hidden.status == 404
    assert cancelled.status == repeated.status == 200
    assert cancelled.body == repeated.body
    assert Order.objects.get(pk=order_id).state == Order.State.CANCELLED
    assert (stock.on_hand, stock.reserved) == (2, 0)
    assert Reservation.objects.get(order_id=order_id).state == Reservation.State.RELEASED
    assert NotificationIntent.objects.filter(order_id=order_id, transition="cancelled").count() == 1


@pytest.mark.django_db(transaction=True)
def test_expiry_prevents_payment_and_releases_stock(shop: tuple[User, Product]) -> None:
    user, product = shop
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk
    Order.objects.filter(pk=order_id).update(expires_at=database_now() - timedelta(seconds=1))

    result = simulate_payment(user=user, order_id=order_id, idempotency_key=uuid4())

    assert result.status == 409
    assert result.body["code"] == "ORDER_EXPIRED"
    assert Order.objects.get(pk=order_id).state == Order.State.EXPIRED
    assert PaymentAttempt.objects.filter(order_id=order_id).count() == 0
    assert (
        StockItem.objects.get(product=product).on_hand,
        StockItem.objects.get(product=product).reserved,
    ) == (2, 0)


@pytest.mark.django_db(transaction=True)
def test_transition_insert_failure_rolls_back_payment_and_reservation(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk

    with patch(
        "modules.notifications.services.NotificationIntent.objects.create",
        side_effect=IntegrityError("fail"),
    ):
        with pytest.raises(IntegrityError):
            simulate_payment(user=user, order_id=order_id, idempotency_key=uuid4())

    assert Order.objects.get(pk=order_id).state == Order.State.AWAITING_PAYMENT
    assert PaymentAttempt.objects.filter(order_id=order_id).count() == 0
    assert IdempotencyRecord.objects.filter(operation="orders.payment").count() == 0
    assert (
        StockItem.objects.get(product=product).on_hand,
        StockItem.objects.get(product=product).reserved,
    ) == (2, 1)


@pytest.mark.django_db(transaction=True)
def test_order_state_and_audit_immutability_are_enforced(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    order_id = UUID(checkout(user, product).body["id"])
    audit = AuditEntry.objects.get(target_id=order_id, action="order.created")

    with pytest.raises(IntegrityError), transaction.atomic():
        Order.objects.filter(pk=order_id).update(state="invented_state")
    with pytest.raises(ValueError, match="append-only"):
        audit.save()
    with pytest.raises(ValueError, match="append-only"):
        audit.delete()


@pytest.mark.django_db(transaction=True)
def test_competing_checkouts_cannot_reserve_last_unit(shop: tuple[User, Product]) -> None:
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock acceptance requires PostgreSQL.")
    user, product = shop
    StockItem.objects.filter(product=product).update(on_hand=1, reserved=0)

    def attempt() -> int:
        connections.close_all()
        try:
            thread_user = User.objects.get(pk=user.pk)
            thread_product = Product.objects.get(pk=product.pk)
            return checkout(thread_user, thread_product).status
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(lambda _: attempt(), range(2)))

    assert statuses == [201, 409]
    stock = StockItem.objects.get(product=product)
    assert (stock.on_hand, stock.reserved, stock.available) == (1, 1, 0)
    assert Order.objects.filter(state=Order.State.AWAITING_PAYMENT).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_key_checkout_replays_single_order(shop: tuple[User, Product]) -> None:
    if connection.vendor != "postgresql":
        pytest.skip("Unique-key contention acceptance requires PostgreSQL.")
    user, product = shop
    key = uuid4()

    def attempt() -> OperationResult:
        connections.close_all()
        try:
            thread_user = User.objects.get(pk=user.pk)
            thread_product = Product.objects.get(pk=product.pk)
            return checkout(thread_user, thread_product, key=key)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))

    assert [result.status for result in results] == [201, 201]
    assert len({result.body["id"] for result in results}) == 1
    assert sorted(result.replayed for result in results) == [False, True]
    assert Order.objects.count() == 1
    assert StockItem.objects.get(product=product).reserved == 1


@pytest.mark.django_db(transaction=True)
def test_payment_waiting_on_order_lock_checks_deadline_after_lock(
    shop: tuple[User, Product],
) -> None:
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL wall-clock/row-lock behavior is required.")
    user, product = shop
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk
    Order.objects.filter(pk=order_id).update(
        expires_at=database_now() + timedelta(milliseconds=250)
    )
    locked = Event()
    release = Event()

    def hold_lock() -> None:
        connections.close_all()
        try:
            with transaction.atomic():
                Order.objects.select_for_update().get(pk=order_id)
                locked.set()
                release.wait(timeout=5)
        finally:
            connections.close_all()

    def attempt_payment() -> OperationResult:
        connections.close_all()
        try:
            thread_user = User.objects.get(pk=user.pk)
            return simulate_payment(user=thread_user, order_id=order_id, idempotency_key=uuid4())
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        holder = pool.submit(hold_lock)
        assert locked.wait(timeout=2)
        time.sleep(0.35)
        payment = pool.submit(attempt_payment)
        time.sleep(0.15)
        release.set()
        holder.result(timeout=3)
        result = payment.result(timeout=3)

    assert result.status == 409
    assert result.body["code"] == "ORDER_EXPIRED"
    assert Order.objects.get(pk=order_id).state == Order.State.EXPIRED


@pytest.mark.django_db(transaction=True)
def test_payment_and_cancellation_race_has_one_terminal_effect(shop: tuple[User, Product]) -> None:
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock acceptance requires PostgreSQL.")
    user, product = shop
    order_id = Order.objects.get(pk=checkout(user, product).body["id"]).pk

    def attempt(action: str) -> OperationResult:
        connections.close_all()
        try:
            thread_user = User.objects.get(pk=user.pk)
            if action == "payment":
                return simulate_payment(
                    user=thread_user, order_id=order_id, idempotency_key=uuid4()
                )
            return cancel_order(user=thread_user, order_id=order_id, idempotency_key=uuid4())
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        payment = pool.submit(attempt, "payment")
        cancellation = pool.submit(attempt, "cancel")
        results = (payment.result(timeout=5), cancellation.result(timeout=5))

    order = Order.objects.get(pk=order_id)
    stock = StockItem.objects.get(product=product)
    assert order.state in (Order.State.CONFIRMED, Order.State.CANCELLED)
    assert sum(result.status == 200 for result in results) == 1
    assert stock.reserved == 0
    if order.state == Order.State.CONFIRMED:
        assert stock.on_hand == 1
        assert PaymentAttempt.objects.filter(order_id=order_id).count() == 1
        assert Reservation.objects.get(order_id=order_id).state == Reservation.State.CONSUMED
    else:
        assert stock.on_hand == 2
        assert PaymentAttempt.objects.filter(order_id=order_id).count() == 0
        assert Reservation.objects.get(order_id=order_id).state == Reservation.State.RELEASED
