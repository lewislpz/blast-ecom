from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.http.response import HttpResponseBase
from django.test import Client, override_settings

from modules.inventory.models import Reservation, StockItem
from modules.inventory.services import adjust_stock
from modules.orders.models import Order
from modules.orders.services import create_order, start_payment
from modules.payments import stripe_provider
from modules.payments.models import PaymentAttempt, ProviderEvent
from modules.payments.stripe_provider import StripeProviderError
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User

WEBHOOK_SECRET = "whsec_test_only_not_a_real_secret"
API_SECRET = "sk_test_not_a_real_secret"
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
    user = User.objects.create_user("stripe-customer@example.test")
    category = Category.objects.create(slug=f"stripe-{uuid4().hex[:8]}", name="Stripe test")
    product = save_product(
        Product(
            sku=f"STRIPE-{uuid4().hex[:8]}",
            category=category,
            title="Snapshot product",
            unit_price=Decimal("9.95"),
        )
    )
    adjust_stock(product_id=product.pk, actor=user, delta=2, reason="Fictional test stock")
    return user, product


def make_order(user: User, product: Product) -> Order:
    result = create_order(
        user=user,
        idempotency_key=uuid4(),
        items=[
            {
                "product_id": str(product.pk),
                "quantity": 1,
                "expected_unit_price": "9.95",
            }
        ],
        address=ADDRESS,
    )
    return Order.objects.get(pk=result.body["id"])


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
    FRONTEND_BASE_URL="http://127.0.0.1:5173",
)
def test_checkout_creation_uses_server_snapshots_and_manual_capture(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    captured: dict[str, object] = {}

    class FakeSessions:
        def create(self, params: dict[str, object], options: dict[str, str]) -> SimpleNamespace:
            captured["params"] = params
            captured["options"] = options
            return SimpleNamespace(
                id="cs_test_session",
                url="https://checkout.stripe.com/c/pay/cs_test_session",
            )

    fake_client = SimpleNamespace(
        v1=SimpleNamespace(checkout=SimpleNamespace(sessions=FakeSessions()))
    )
    monkeypatch.setattr(stripe_provider, "_client", lambda: fake_client)
    attempt = PaymentAttempt.objects.create(
        order=order,
        provider=PaymentAttempt.Provider.STRIPE,
        outcome=PaymentAttempt.Outcome.PENDING,
        amount=order.total,
        currency=order.currency,
        simulator_reference=None,
    )

    session_id, session_url = stripe_provider.create_checkout_session(order=order, attempt=attempt)

    assert session_id == "cs_test_session"
    assert session_url == "https://checkout.stripe.com/c/pay/cs_test_session"
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["payment_method_types"] == ["card"]
    assert params["line_items"] == [
        {
            "quantity": 1,
            "price_data": {
                "currency": "eur",
                "unit_amount": 995,
                "product_data": {"name": "Snapshot product"},
            },
        }
    ]
    assert params["payment_intent_data"] == {
        "capture_method": "manual",
        "metadata": {"order_id": str(order.pk), "payment_attempt_id": str(attempt.pk)},
    }
    assert params["success_url"] == f"http://127.0.0.1:5173/orders/{order.pk}?payment=return"
    assert captured["options"] == {"idempotency_key": f"blast-ecom-checkout-{attempt.pk}"}
    serialized = json.dumps(params).lower()
    assert "card_number" not in serialized
    assert "card_details" not in serialized
    assert "cvc" not in serialized


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
    FRONTEND_BASE_URL="https://shop.example.test",
)
def test_start_payment_is_owner_scoped_and_idempotent(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    calls = 0

    def create_session(*, order: Order, attempt: PaymentAttempt) -> tuple[str, str]:
        nonlocal calls
        calls += 1
        assert order.total == Decimal("9.95")
        return "cs_test_one", "https://checkout.stripe.com/c/pay/cs_test_one"

    monkeypatch.setattr("modules.orders.services.create_checkout_session", create_session)
    key = uuid4()
    first = start_payment(user=user, order_id=order.pk, idempotency_key=key)
    replay = start_payment(user=user, order_id=order.pk, idempotency_key=key)

    assert first.status == replay.status == 200
    assert first.body == replay.body
    assert first.body["checkout_url"] == "https://checkout.stripe.com/c/pay/cs_test_one"
    assert calls == 1
    attempt = PaymentAttempt.objects.get(order=order)
    assert attempt.provider == PaymentAttempt.Provider.STRIPE
    assert attempt.amount == order.total
    assert attempt.provider_session_id == "cs_test_one"
    assert attempt.outcome == PaymentAttempt.Outcome.PENDING
    assert Reservation.objects.get(order=order).state == Reservation.State.ACTIVE


def make_signature(payload: bytes, *, timestamp: int | None = None) -> str:
    event_time = timestamp or int(time.time())
    signed = str(event_time).encode() + b"." + payload
    digest = hmac.new(WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={event_time},v1={digest}"


def authorization_payload(
    attempt: PaymentAttempt,
    *,
    event_id: str = "evt_test_authorized",
    amount: int = 995,
    amount_capturable: int = 995,
    payment_intent_id: str = "pi_test_authorized",
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "object": "event",
            "type": "payment_intent.amount_capturable_updated",
            "data": {
                "object": {
                    "id": payment_intent_id,
                    "object": "payment_intent",
                    "status": "requires_capture",
                    "amount": amount,
                    "amount_capturable": amount_capturable,
                    "currency": "eur",
                    "metadata": {
                        "order_id": str(attempt.order_id),
                        "payment_attempt_id": str(attempt.pk),
                    },
                }
            },
        },
        separators=(",", ":"),
    ).encode()


def send_webhook(payload: bytes, signature: str) -> HttpResponseBase:
    return Client().post(
        "/api/v1/payments/stripe/webhook/",
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=signature,
    )


def create_pending_attempt(order: Order) -> PaymentAttempt:
    return PaymentAttempt.objects.create(
        order=order,
        provider=PaymentAttempt.Provider.STRIPE,
        outcome=PaymentAttempt.Outcome.PENDING,
        amount=order.total,
        currency=order.currency,
        simulator_reference=None,
    )


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
)
def test_signed_authorization_is_captured_once_and_duplicate_event_is_ignored(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    attempt = create_pending_attempt(order)
    captured: list[str] = []

    def capture(*, payment_intent_id: str) -> SimpleNamespace:
        captured.append(payment_intent_id)
        return SimpleNamespace(status="succeeded", amount_received=995, currency="eur")

    monkeypatch.setattr("modules.orders.services.capture_payment_intent", capture)
    payload = authorization_payload(attempt)
    signature = make_signature(payload)
    second_authorization = authorization_payload(
        attempt,
        event_id="evt_test_authorized_redelivery",
    )

    first = send_webhook(payload, signature)
    duplicate = send_webhook(payload, signature)
    later_delivery = send_webhook(
        second_authorization,
        make_signature(second_authorization),
    )

    assert first.status_code == duplicate.status_code == later_delivery.status_code == 204
    order.refresh_from_db()
    attempt.refresh_from_db()
    assert order.state == Order.State.CONFIRMED
    assert attempt.outcome == PaymentAttempt.Outcome.SUCCEEDED
    assert attempt.provider_payment_intent_id == "pi_test_authorized"
    assert ProviderEvent.objects.filter(status=ProviderEvent.Status.PROCESSED).count() == 2
    stock = StockItem.objects.get(product=product)
    assert (stock.on_hand, stock.reserved) == (1, 0)
    assert captured == ["pi_test_authorized"]


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
)
def test_capture_failure_keeps_event_retryable_and_finalizes_on_provider_retry(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    attempt = create_pending_attempt(order)
    calls = 0

    def capture(*, payment_intent_id: str) -> SimpleNamespace:
        nonlocal calls
        assert payment_intent_id == "pi_test_authorized"
        calls += 1
        if calls == 1:
            raise StripeProviderError("Temporary provider failure.")
        return SimpleNamespace(status="succeeded", amount_received=995, currency="eur")

    monkeypatch.setattr("modules.orders.services.capture_payment_intent", capture)
    payload = authorization_payload(attempt)
    signature = make_signature(payload)

    failed_delivery = send_webhook(payload, signature)
    event = ProviderEvent.objects.get(provider_event_id="evt_test_authorized")
    order.refresh_from_db()
    attempt.refresh_from_db()
    assert failed_delivery.status_code == 503
    assert event.status == ProviderEvent.Status.PENDING
    assert event.action == ProviderEvent.Action.CAPTURE
    assert order.state == Order.State.PAYMENT_PROCESSING
    assert attempt.outcome == PaymentAttempt.Outcome.CAPTURING
    assert StockItem.objects.get(product=product).reserved == 1

    retried_delivery = send_webhook(payload, signature)

    assert retried_delivery.status_code == 204
    event.refresh_from_db()
    order.refresh_from_db()
    attempt.refresh_from_db()
    assert event.status == ProviderEvent.Status.PROCESSED
    assert order.state == Order.State.CONFIRMED
    assert attempt.outcome == PaymentAttempt.Outcome.SUCCEEDED
    assert (
        StockItem.objects.get(product=product).on_hand,
        StockItem.objects.get(product=product).reserved,
    ) == (1, 0)
    assert calls == 2


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
)
def test_conflicting_payload_for_processed_provider_event_is_rejected(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    attempt = create_pending_attempt(order)
    monkeypatch.setattr(
        "modules.orders.services.capture_payment_intent",
        lambda *, payment_intent_id: SimpleNamespace(
            status="succeeded", amount_received=995, currency="eur"
        ),
    )
    first_payload = authorization_payload(attempt)
    first = send_webhook(first_payload, make_signature(first_payload))
    conflicting_payload = authorization_payload(attempt, amount=1095, amount_capturable=1095)
    conflict = send_webhook(
        conflicting_payload,
        make_signature(conflicting_payload),
    )

    assert first.status_code == 204
    assert conflict.status_code == 400
    assert Order.objects.get(pk=order.pk).state == Order.State.CONFIRMED
    assert PaymentAttempt.objects.get(pk=attempt.pk).outcome == PaymentAttempt.Outcome.SUCCEEDED
    assert ProviderEvent.objects.count() == 1


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
)
def test_invalid_signature_has_no_payment_side_effects(shop: tuple[User, Product]) -> None:
    user, product = shop
    order = make_order(user, product)
    attempt = create_pending_attempt(order)
    payload = authorization_payload(attempt)

    response = send_webhook(payload, "t=1,v1=invalid")

    assert response.status_code == 400
    assert ProviderEvent.objects.count() == 0
    assert PaymentAttempt.objects.get(pk=attempt.pk).outcome == PaymentAttempt.Outcome.PENDING
    assert Order.objects.get(pk=order.pk).state == Order.State.AWAITING_PAYMENT
    assert StockItem.objects.get(product=product).reserved == 1


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
)
def test_late_or_amount_mismatched_authorization_is_cancelled_not_captured(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    attempt = create_pending_attempt(order)
    cancellations: list[str] = []

    def cancel(*, payment_intent_id: str) -> SimpleNamespace:
        cancellations.append(payment_intent_id)
        return SimpleNamespace(status="canceled")

    monkeypatch.setattr("modules.orders.services.cancel_payment_intent", cancel)
    payload = authorization_payload(attempt, amount=1095, amount_capturable=1095)
    response = send_webhook(payload, make_signature(payload))

    assert response.status_code == 204
    order.refresh_from_db()
    attempt.refresh_from_db()
    assert order.state == Order.State.FAILED
    assert attempt.outcome == PaymentAttempt.Outcome.FAILED
    assert Reservation.objects.get(order=order).state == Reservation.State.RELEASED
    assert StockItem.objects.get(product=product).reserved == 0
    assert cancellations == ["pi_test_authorized"]
    assert ProviderEvent.objects.get(provider_event_id="evt_test_authorized").action == (
        ProviderEvent.Action.CANCEL
    )


@pytest.mark.django_db(transaction=True)
@override_settings(
    DEBUG=True,
    PAYMENT_PROVIDER="stripe_sandbox",
    STRIPE_SECRET_KEY=API_SECRET,
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
)
def test_authorization_after_expiry_releases_stock_and_never_captures(
    shop: tuple[User, Product], monkeypatch: pytest.MonkeyPatch
) -> None:
    user, product = shop
    order = make_order(user, product)
    attempt = create_pending_attempt(order)
    order.expires_at -= timedelta(minutes=30)
    order.save(update_fields=["expires_at", "updated_at"])
    cancellations: list[str] = []

    def cancel(*, payment_intent_id: str) -> SimpleNamespace:
        cancellations.append(payment_intent_id)
        return SimpleNamespace(status="canceled")

    monkeypatch.setattr("modules.orders.services.cancel_payment_intent", cancel)
    payload = authorization_payload(attempt)

    response = send_webhook(payload, make_signature(payload))

    assert response.status_code == 204
    order.refresh_from_db()
    assert order.state == Order.State.EXPIRED
    assert Reservation.objects.get(order=order).state == Reservation.State.RELEASED
    assert StockItem.objects.get(product=product).reserved == 0
    assert cancellations == ["pi_test_authorized"]
