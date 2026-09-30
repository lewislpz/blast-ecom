from django.db.models import Exists, F, OuterRef, QuerySet

from modules.inventory.models import StockItem
from modules.products.models import Category, Product


def active_categories() -> QuerySet[Category]:
    return Category.objects.filter(active=True).order_by("name", "id")


def active_products() -> QuerySet[Product]:
    available_stock = StockItem.objects.filter(
        product_id=OuterRef("pk"),
        on_hand__gt=F("reserved"),
    )
    return (
        Product.objects.filter(active=True, category__active=True)
        .select_related("category")
        .annotate(in_stock=Exists(available_stock))
    )
