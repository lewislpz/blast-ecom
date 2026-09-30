from __future__ import annotations

import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from modules.common.audit import record_audit
from modules.common.operations import OperationResult, database_now, execute_idempotent
from modules.inventory.models import StockItem
from modules.inventory.services import (
    reserve_for_order,
    transition_order_reservations,
)
from modules.notifications.services import create_transition_intent
from modules.orders.models import Order, OrderItem
from modules.payments.selectors import get_payment_attempt
from modules.payments.services import create_simulated_attempt
from modules.products.models import Product
from modules.users.models import User

MAX_LINES = 50
MAX_QUANTITY = 99
MAX_AMOUNT = Decimal("9999999999.99")
COUNTRY_CODE = re.compile(r"^[A-Z]{2}$")
EXPECTED_PRICE = re.compile(r"^(?:0|[1-9]\d{0,9})\.\d{2}$")
ADDRESS_LIMITS = {
    "recipient": 160,
    "address_line_1": 200,
    "address_line_2": 200,
    "city": 120,
    "region": 120,
    "postal_code": 32,
}


class CheckoutInputError(ValueError):
    """Raised for invalid checkout data before an idempotency record is created."""


def _normalize_checkout(
    items: list[dict[str, Any]], address: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if not isinstance(items, list) or not items or len(items) > MAX_LINES:
        raise CheckoutInputError("Checkout must contain between 1 and 50 lines.")

    normalized_items: list[dict[str, Any]] = []
    seen: set[UUID] = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {
            "product_id",
            "quantity",
            "expected_unit_price",
        }:
            raise CheckoutInputError(
                "Each line must contain only product_id, quantity and expected_unit_price."
            )
        raw_price = item["expected_unit_price"]
        if not isinstance(raw_price, str) or EXPECTED_PRICE.fullmatch(raw_price) is None:
            raise CheckoutInputError("Expected unit price must use a two-decimal string.")
        try:
            product_id = UUID(str(item["product_id"]))
            quantity = item["quantity"]
            price = Decimal(raw_price)
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise CheckoutInputError(
                "Each line needs a product, quantity and expected price."
            ) from exc
        if product_id in seen:
            raise CheckoutInputError("Duplicate product lines are not allowed.")
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or not 1 <= quantity <= MAX_QUANTITY
        ):
            raise CheckoutInputError("Quantity must be an integer from 1 to 99.")
        if (
            not price.is_finite()
            or price <= 0
            or price > MAX_AMOUNT
            or price != price.quantize(Decimal("0.01"))
        ):
            raise CheckoutInputError("Expected unit price must be a positive two-decimal amount.")
        normalized_items.append(
            {
                "product_id": str(product_id),
                "quantity": quantity,
                "expected_unit_price": format(price, ".2f"),
            }
        )
        seen.add(product_id)
    normalized_items.sort(key=lambda line: line["product_id"])

    if not isinstance(address, dict):
        raise CheckoutInputError("A delivery address is required.")
    unknown_address_fields = set(address) - (set(ADDRESS_LIMITS) | {"country_code"})
    if unknown_address_fields:
        raise CheckoutInputError("Address contains unsupported fields.")
    normalized_address: dict[str, str] = {}
    required = ("recipient", "address_line_1", "city", "country_code")
    for field, maximum in ADDRESS_LIMITS.items():
        value = address.get(field, "")
        if not isinstance(value, str):
            raise CheckoutInputError(f"{field} must be text.")
        value = value.strip()
        if len(value) > maximum or (field in required and not value):
            raise CheckoutInputError(f"{field} is required and limited to {maximum} characters.")
        normalized_address[field] = value
    country = address.get("country_code")
    if not isinstance(country, str) or COUNTRY_CODE.fullmatch(country) is None:
        raise CheckoutInputError("country_code must be an uppercase ISO alpha-2 code.")
    normalized_address["country_code"] = country
    return normalized_items, normalized_address


def _order_body(order: Order) -> dict[str, Any]:
    return {
        "id": str(order.pk),
        "state": str(order.state),
        "currency": order.currency,
        "subtotal": format(order.subtotal, ".2f"),
        "shipping_total": format(order.shipping_total, ".2f"),
        "total": format(order.total, ".2f"),
        "expires_at": order.expires_at.isoformat(),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "items": [
            {
                "product_id": str(item.product_id),
                "sku": item.sku_snapshot,
                "title": item.title_snapshot,
                "unit_price": format(item.unit_price, ".2f"),
                "quantity": item.quantity,
                "line_total": format(item.line_total, ".2f"),
            }
            for item in order.items.order_by("product_id")
        ],
    }


def _record_transition(*, order: Order, actor: User | None, previous: str, action: str) -> None:
    record_audit(
        actor=actor,
        action=action,
        target_id=order.pk,
        metadata={"from_state": previous, "to_state": order.state},
    )
    create_transition_intent(order=order)


@transaction.atomic
def create_order(
    *, user: User, idempotency_key: UUID, items: list[dict[str, Any]], address: dict[str, Any]
) -> OperationResult:
    normalized_items, normalized_address = _normalize_checkout(items, address)
    payload = {"items": normalized_items, "address": normalized_address}

    def execute() -> OperationResult:
        requested_ids = [UUID(line["product_id"]) for line in normalized_items]
        products = list(
            Product.objects.select_for_update()
            .filter(pk__in=requested_ids, active=True, category__active=True)
            .order_by("pk")
        )
        by_id = {product.pk: product for product in products}
        if len(by_id) != len(requested_ids):
            return OperationResult(409, {"code": "PRODUCT_UNAVAILABLE"})
        for line in normalized_items:
            product = by_id[UUID(line["product_id"])]
            if format(product.unit_price, ".2f") != line["expected_unit_price"]:
                return OperationResult(
                    409, {"code": "PRICE_CHANGED", "product_id": str(product.pk)}
                )

        quantities = {UUID(line["product_id"]): line["quantity"] for line in normalized_items}
        stock_items = list(
            StockItem.objects.select_for_update()
            .filter(product_id__in=requested_ids)
            .order_by("product_id")
        )
        stock_by_product = {stock.product_id: stock for stock in stock_items}
        if len(stock_by_product) != len(requested_ids) or any(
            stock_by_product[product_id].available < quantities[product_id]
            for product_id in requested_ids
        ):
            return OperationResult(409, {"code": "OUT_OF_STOCK"})

        subtotal = sum(
            (
                by_id[UUID(line["product_id"])].unit_price * line["quantity"]
                for line in normalized_items
            ),
            Decimal("0.00"),
        )
        if subtotal > MAX_AMOUNT:
            raise CheckoutInputError("Order total exceeds the supported amount.")
        now = database_now()
        timeout = int(getattr(settings, "BLAST_ECOM_RESERVATION_MINUTES", 15))
        order = Order.objects.create(
            customer=user,
            state=Order.State.AWAITING_PAYMENT,
            currency="EUR",
            subtotal=subtotal,
            shipping_total=Decimal("0.00"),
            total=subtotal,
            expires_at=now + timedelta(minutes=timeout),
            **normalized_address,
        )
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=by_id[UUID(line["product_id"])],
                    sku_snapshot=by_id[UUID(line["product_id"])].sku,
                    title_snapshot=by_id[UUID(line["product_id"])].title,
                    unit_price=by_id[UUID(line["product_id"])].unit_price,
                    quantity=line["quantity"],
                    line_total=by_id[UUID(line["product_id"])].unit_price * line["quantity"],
                )
                for line in normalized_items
            ]
        )
        reserve_for_order(order_id=order.pk, quantities=quantities)
        record_audit(
            actor=user,
            action="order.created",
            target_id=order.pk,
            metadata={"state": order.state},
        )
        return OperationResult(201, _order_body(order))

    return execute_idempotent(
        user=user,
        operation="orders.create",
        key=idempotency_key,
        payload=payload,
        execute=execute,
    )


def _locked_owned_order(*, order_id: UUID, user: User) -> Order | None:
    return Order.objects.select_for_update().filter(pk=order_id, customer=user).first()


def _expire_locked_order(order: Order, *, actor: User | None) -> bool:
    if order.state != Order.State.AWAITING_PAYMENT or order.expires_at > database_now():
        return False
    previous = order.state
    transition_order_reservations(order_id=order.pk, consume=False)
    order.state = Order.State.EXPIRED
    order.transitioned_at = database_now()
    order.save(update_fields=["state", "transitioned_at", "updated_at"])
    _record_transition(order=order, actor=actor, previous=previous, action="order.expired")
    return True


@transaction.atomic
def cancel_order(*, user: User, order_id: UUID, idempotency_key: UUID) -> OperationResult:
    payload = {"order_id": str(order_id)}

    def execute() -> OperationResult:
        order = _locked_owned_order(order_id=order_id, user=user)
        if order is None:
            return OperationResult(404, {"code": "NOT_FOUND"})
        if _expire_locked_order(order, actor=user):
            return OperationResult(409, {"code": "ORDER_EXPIRED", "order": _order_body(order)})
        if order.state == Order.State.CANCELLED:
            return OperationResult(200, _order_body(order))
        if order.state != Order.State.AWAITING_PAYMENT:
            return OperationResult(409, {"code": "ORDER_NOT_CANCELLABLE", "state": order.state})
        previous = order.state
        transition_order_reservations(order_id=order.pk, consume=False)
        order.state = Order.State.CANCELLED
        order.transitioned_at = database_now()
        order.save(update_fields=["state", "transitioned_at", "updated_at"])
        _record_transition(order=order, actor=user, previous=previous, action="order.cancelled")
        return OperationResult(200, _order_body(order))

    return execute_idempotent(
        user=user,
        operation="orders.cancel",
        key=idempotency_key,
        payload=payload,
        execute=execute,
        authorize_replay=lambda: Order.objects.filter(pk=order_id, customer=user).exists(),
    )


def get_owned_order(*, user: User, order_id: UUID) -> Order | None:
    return Order.objects.filter(customer=user, pk=order_id).prefetch_related("items").first()


def owned_orders(*, user: User) -> QuerySet[Order]:
    return Order.objects.filter(customer=user).prefetch_related("items")


def _payment_body(order: Order, attempt: Any | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "order_id": str(order.pk),
        "order_state": str(order.state),
        "total": format(order.total, ".2f"),
        "currency": order.currency,
    }
    if attempt is not None:
        body["payment"] = {"id": str(attempt.pk), "outcome": attempt.outcome}
    return body


@transaction.atomic
def simulate_payment(*, user: User, order_id: UUID, idempotency_key: UUID) -> OperationResult:
    payload = {"order_id": str(order_id), "command": "simulate_payment"}

    def execute() -> OperationResult:
        order = _locked_owned_order(order_id=order_id, user=user)
        if order is None:
            return OperationResult(404, {"code": "NOT_FOUND"})
        if _expire_locked_order(order, actor=user):
            return OperationResult(409, {"code": "ORDER_EXPIRED", "order": _payment_body(order)})

        existing = get_payment_attempt(order_id=order.pk)
        if existing is not None:
            if order.state in (Order.State.CONFIRMED, Order.State.FAILED):
                return OperationResult(200, _payment_body(order, existing))
            return OperationResult(409, {"code": "PAYMENT_ALREADY_RECORDED"})
        if order.state != Order.State.AWAITING_PAYMENT:
            return OperationResult(409, {"code": "ORDER_NOT_PAYABLE", "state": order.state})

        attempt = create_simulated_attempt(order=order)
        previous = order.state
        if attempt.outcome == "succeeded":
            transition_order_reservations(order_id=order.pk, consume=True)
            order.state = Order.State.CONFIRMED
            action = "payment.succeeded"
        else:
            transition_order_reservations(order_id=order.pk, consume=False)
            order.state = Order.State.FAILED
            action = "payment.failed"
        order.transitioned_at = database_now()
        order.save(update_fields=["state", "transitioned_at", "updated_at"])
        _record_transition(order=order, actor=user, previous=previous, action=action)
        return OperationResult(200, _payment_body(order, attempt))

    return execute_idempotent(
        user=user,
        operation="orders.payment",
        key=idempotency_key,
        payload=payload,
        execute=execute,
        authorize_replay=lambda: Order.objects.filter(pk=order_id, customer=user).exists(),
    )


@transaction.atomic
def expire_order(*, order_id: UUID) -> bool:
    order = Order.objects.select_for_update().filter(pk=order_id).first()
    if order is None:
        return False
    return _expire_locked_order(order, actor=None)


def expire_due_orders(*, limit: int = 100) -> int:
    if not 1 <= limit <= 1000:
        raise ValueError("Expiry batch limit must be between 1 and 1000.")
    candidate_ids = list(
        Order.objects.filter(state=Order.State.AWAITING_PAYMENT, expires_at__lte=database_now())
        .order_by("expires_at", "id")
        .values_list("id", flat=True)[:limit]
    )
    expired = 0
    for order_id in candidate_ids:
        if expire_order(order_id=order_id):
            expired += 1
    return expired
