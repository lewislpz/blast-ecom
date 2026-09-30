from rest_framework import serializers

from modules.products.models import Category, Product


class CategorySerializer(serializers.ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ("id", "slug", "name")


class ProductSerializer(serializers.ModelSerializer[Product]):
    category = CategorySerializer(read_only=True)
    in_stock = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "title",
            "description",
            "category",
            "unit_price",
            "currency",
            "in_stock",
            "image_key",
        )

    def get_currency(self, obj: Product) -> str:
        return "EUR"

    def get_in_stock(self, obj: Product) -> bool:
        return bool(getattr(obj, "in_stock", False))
