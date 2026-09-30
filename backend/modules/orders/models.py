import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Order(models.Model):
    class State(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    state = models.CharField(max_length=24, choices=State.choices, default=State.AWAITING_PAYMENT)
    currency = models.CharField(max_length=3, default="EUR")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2)
    recipient = models.CharField(max_length=160)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    country_code = models.CharField(max_length=2)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transitioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(
                fields=("customer", "-created_at", "-id"), name="orders_owner_created_idx"
            ),
            models.Index(fields=("state", "expires_at"), name="orders_state_expiry_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    state__in=["awaiting_payment", "confirmed", "failed", "cancelled", "expired"]
                ),
                name="orders_state_valid",
            ),
            models.CheckConstraint(condition=Q(currency="EUR"), name="orders_currency_eur"),
            models.CheckConstraint(
                condition=Q(total=F("subtotal") + F("shipping_total")),
                name="orders_total_matches_components",
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0), name="orders_subtotal_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(shipping_total__gte=0), name="orders_shipping_nonnegative"
            ),
        ]


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    sku_snapshot = models.CharField(max_length=64)
    title_snapshot = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("order", "product"), name="orders_item_order_product_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="orders_item_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gt=0), name="orders_item_price_positive"
            ),
            models.CheckConstraint(
                condition=Q(line_total=F("unit_price") * F("quantity")),
                name="orders_item_total_matches",
            ),
        ]
