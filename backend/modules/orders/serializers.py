from __future__ import annotations

from typing import Any

from rest_framework import serializers

from modules.common.strict_serializers import StrictSerializer
from modules.orders.models import Order, OrderItem


class OrderLineInputSerializer(StrictSerializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=99)
    expected_unit_price = serializers.RegexField(
        regex=r"^(?:0|[1-9]\d{0,9})\.\d{2}$", max_length=13
    )


class DeliveryAddressInputSerializer(StrictSerializer):
    recipient = serializers.CharField(max_length=160, allow_blank=False, trim_whitespace=True)
    address_line_1 = serializers.CharField(max_length=200, allow_blank=False, trim_whitespace=True)
    address_line_2 = serializers.CharField(max_length=200, allow_blank=True, required=False)
    city = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    region = serializers.CharField(max_length=120, allow_blank=True, required=False)
    postal_code = serializers.CharField(max_length=32, allow_blank=True, required=False)
    country_code = serializers.RegexField(regex=r"^[A-Z]{2}$", max_length=2)


class CreateOrderRequestSerializer(StrictSerializer):
    items = serializers.ListField(
        child=OrderLineInputSerializer(), allow_empty=False, max_length=50
    )
    delivery_address = DeliveryAddressInputSerializer()


class OrderItemResponseSerializer(serializers.ModelSerializer[OrderItem]):
    product_id = serializers.UUIDField(read_only=True)
    sku = serializers.CharField(source="sku_snapshot", read_only=True)
    title = serializers.CharField(source="title_snapshot", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("product_id", "sku", "title", "unit_price", "quantity", "line_total")


class OrderOperationResponseSerializer(serializers.Serializer[Any]):
    id = serializers.UUIDField()
    state = serializers.CharField()
    currency = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    shipping_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    expires_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    items = OrderItemResponseSerializer(many=True)


class PaymentOperationResponseSerializer(serializers.Serializer[Any]):
    order_id = serializers.UUIDField()
    order_state = serializers.CharField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    payment = serializers.DictField(required=False)


class DeliveryAddressResponseSerializer(serializers.Serializer[Any]):
    recipient = serializers.CharField()
    address_line_1 = serializers.CharField()
    address_line_2 = serializers.CharField(allow_blank=True)
    city = serializers.CharField()
    region = serializers.CharField(allow_blank=True)
    postal_code = serializers.CharField(allow_blank=True)
    country_code = serializers.CharField()


class OrderDetailResponseSerializer(serializers.Serializer[Any]):
    id = serializers.UUIDField()
    state = serializers.CharField()
    currency = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    shipping_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    expires_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    items = OrderItemResponseSerializer(many=True)
    delivery_address = serializers.SerializerMethodField()

    def get_delivery_address(self, obj: Order) -> dict[str, str]:
        return {
            "recipient": obj.recipient,
            "address_line_1": obj.address_line_1,
            "address_line_2": obj.address_line_2,
            "city": obj.city,
            "region": obj.region,
            "postal_code": obj.postal_code,
            "country_code": obj.country_code,
        }


class AccountOrderListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = OrderOperationResponseSerializer(many=True)
