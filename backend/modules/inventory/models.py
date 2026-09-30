import uuid
from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class StockItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_item",
    )
    on_hand = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    reserved = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(on_hand__gte=0), name="inventory_stock_on_hand_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(reserved__gte=0), name="inventory_stock_reserved_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(reserved__lte=F("on_hand")),
                name="inventory_stock_reserved_lte_on_hand",
            ),
        ]

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class StockAdjustment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_adjustments",
    )
    delta = models.IntegerField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_adjustments",
    )
    reason = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")
        permissions = [("adjust_stock", "Can adjust inventory stock")]
        constraints = [
            models.CheckConstraint(
                condition=~Q(delta=0), name="inventory_adjustment_delta_nonzero"
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValueError("Stock adjustments are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValueError("Stock adjustments are append-only.")


class Reservation(models.Model):
    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        CONSUMED = "consumed", "Consumed"
        RELEASED = "released", "Released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="reservations")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="reservations"
    )
    quantity = models.PositiveSmallIntegerField()
    state = models.CharField(max_length=12, choices=State.choices, default=State.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    transitioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("order", "product"), name="inventory_order_product_reservation_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="inventory_reservation_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(state__in=["active", "consumed", "released"]),
                name="inventory_reservation_state_valid",
            ),
        ]
