from uuid import UUID

from django.db import transaction

from modules.common.operations import database_now
from modules.inventory.models import Reservation, StockAdjustment, StockItem
from modules.users.models import User


class StockAdjustmentRejected(ValueError):
    """Raised when an adjustment would violate the stock invariants."""


class StockUnavailable(ValueError):
    """Raised when requested units cannot be reserved."""


@transaction.atomic
def ensure_stock_item(*, product_id: UUID) -> StockItem:
    stock_item, _ = StockItem.objects.get_or_create(product_id=product_id)
    return stock_item


@transaction.atomic
def adjust_stock(
    *,
    product_id: UUID,
    actor: User,
    delta: int,
    reason: str,
) -> StockAdjustment:
    if isinstance(delta, bool) or not isinstance(delta, int) or delta == 0:
        raise StockAdjustmentRejected("Stock adjustment delta must be a nonzero integer.")

    normalized_reason = reason.strip()
    if not normalized_reason or len(normalized_reason) > 300:
        raise StockAdjustmentRejected("A reason of 1 to 300 characters is required.")

    try:
        stock_item = StockItem.objects.select_for_update().get(product_id=product_id)
    except StockItem.DoesNotExist as exc:
        raise StockAdjustmentRejected("The product has no inventory record.") from exc

    new_on_hand = stock_item.on_hand + delta
    if new_on_hand < stock_item.reserved:
        raise StockAdjustmentRejected("On-hand stock cannot be lower than reserved stock.")

    stock_item.on_hand = new_on_hand
    stock_item.save(update_fields=["on_hand", "updated_at"])
    return StockAdjustment.objects.create(
        product_id=product_id,
        actor=actor,
        delta=delta,
        reason=normalized_reason,
    )


@transaction.atomic
def reserve_for_order(*, order_id: UUID, quantities: dict[UUID, int]) -> None:
    """Reserve each product after callers have locked product rows in UUID order."""
    product_ids = sorted(quantities, key=str)
    stocks = list(
        StockItem.objects.select_for_update()
        .filter(product_id__in=product_ids)
        .order_by("product_id")
    )
    by_product = {stock.product_id: stock for stock in stocks}
    if len(by_product) != len(product_ids):
        raise StockUnavailable("Inventory is not initialized for every product.")
    if any(by_product[product_id].available < quantities[product_id] for product_id in product_ids):
        raise StockUnavailable("One or more requested quantities are unavailable.")

    for product_id in product_ids:
        stock = by_product[product_id]
        quantity = quantities[product_id]
        stock.reserved += quantity
        stock.save(update_fields=["reserved", "updated_at"])
        Reservation.objects.create(order_id=order_id, product_id=product_id, quantity=quantity)


@transaction.atomic
def transition_order_reservations(*, order_id: UUID, consume: bool) -> None:
    """Consume or release active reservations; caller must already hold the order lock."""
    reservations = list(
        Reservation.objects.filter(order_id=order_id, state=Reservation.State.ACTIVE).order_by(
            "product_id"
        )
    )
    product_ids = [reservation.product_id for reservation in reservations]
    stocks = list(
        StockItem.objects.select_for_update()
        .filter(product_id__in=product_ids)
        .order_by("product_id")
    )
    by_product = {stock.product_id: stock for stock in stocks}
    if len(by_product) != len(product_ids):
        raise StockAdjustmentRejected("Reservation inventory record is missing.")

    for reservation in reservations:
        stock = by_product[reservation.product_id]
        if stock.reserved < reservation.quantity:
            raise StockAdjustmentRejected("Reserved stock counter is inconsistent.")
        stock.reserved -= reservation.quantity
        if consume:
            if stock.on_hand < reservation.quantity:
                raise StockAdjustmentRejected("On-hand stock counter is inconsistent.")
            stock.on_hand -= reservation.quantity
        stock.save(update_fields=["on_hand", "reserved", "updated_at"])
        reservation.state = Reservation.State.CONSUMED if consume else Reservation.State.RELEASED
        reservation.transitioned_at = database_now()
        reservation.save(update_fields=["state", "transitioned_at"])
