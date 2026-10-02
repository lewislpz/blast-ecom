"""Narrow Stripe adapter. Provider calls are intentionally outside DB transactions."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

import stripe
from django.conf import settings

from modules.orders.models import Order
from modules.payments.models import PaymentAttempt


class StripeProviderError(RuntimeError):
    """A provider response could not be safely used by the application."""


def amount_in_minor_units(amount: Decimal) -> int:
    minor = amount * 100
    if minor != minor.to_integral_value() or minor <= 0:
        raise StripeProviderError("Payment amount must be a positive whole number of euro cents.")
    return int(minor)


def _client() -> stripe.StripeClient:
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY, max_network_retries=0)


def create_checkout_session(*, order: Order, attempt: PaymentAttempt) -> tuple[str, str]:
    """Create one hosted Checkout Session from immutable server-side order lines."""
    items = list(order.items.order_by("id"))
    metadata = {"order_id": str(order.pk), "payment_attempt_id": str(attempt.pk)}
    line_items: list[dict[str, Any]] = []
    expected_amount = 0
    for item in items:
        unit_amount = amount_in_minor_units(item.unit_price)
        line_items.append(
            {
                "quantity": item.quantity,
                "price_data": {
                    "currency": order.currency.lower(),
                    "unit_amount": unit_amount,
                    "product_data": {"name": item.title_snapshot},
                },
            }
        )
        expected_amount += unit_amount * item.quantity
    if expected_amount != amount_in_minor_units(order.total):
        raise StripeProviderError("Order line snapshots do not match the payable total.")

    frontend = settings.FRONTEND_BASE_URL.rstrip("/")
    params: Any = {
        "mode": "payment",
        "ui_mode": "hosted",
        "payment_method_types": ["card"],
        "line_items": line_items,
        "client_reference_id": str(order.pk),
        "metadata": metadata,
        "payment_intent_data": {
            "capture_method": "manual",
            "metadata": metadata,
        },
        "success_url": f"{frontend}/orders/{order.pk}?payment=return",
        "cancel_url": f"{frontend}/orders/{order.pk}?payment=cancelled",
    }
    session = _client().v1.checkout.sessions.create(
        params,
        {"idempotency_key": f"blast-ecom-checkout-{attempt.pk}"},
    )
    session_id = str(session.id or "")
    session_url = str(session.url or "")
    parsed = urlsplit(session_url)
    if (
        not session_id
        or parsed.scheme != "https"
        or parsed.hostname != "checkout.stripe.com"
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise StripeProviderError("Stripe returned an invalid hosted Checkout Session.")
    return session_id, session_url


def capture_payment_intent(*, payment_intent_id: str) -> stripe.PaymentIntent:
    return _client().v1.payment_intents.capture(
        payment_intent_id,
        {},
        {"idempotency_key": f"blast-ecom-capture-{payment_intent_id}"},
    )


def cancel_payment_intent(*, payment_intent_id: str) -> stripe.PaymentIntent:
    return _client().v1.payment_intents.cancel(
        payment_intent_id,
        {"cancellation_reason": "requested_by_customer"},
        {"idempotency_key": f"blast-ecom-cancel-{payment_intent_id}"},
    )


def expire_checkout_session(*, session_id: str) -> stripe.checkout.Session:
    return _client().v1.checkout.sessions.expire(
        session_id,
        {},
        {"idempotency_key": f"blast-ecom-expire-{session_id}"},
    )
