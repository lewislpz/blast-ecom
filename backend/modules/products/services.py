from django.db import transaction

from modules.products.models import Category, Product


@transaction.atomic
def save_category(category: Category) -> Category:
    category.full_clean()
    category.save()
    return category


@transaction.atomic
def save_product(product: Product) -> Product:
    is_new = product._state.adding
    if is_new:
        product.full_clean()
        product.save()

        # Product creation and its initial zero-stock record are one operation.
        from modules.inventory.services import ensure_stock_item

        ensure_stock_item(product_id=product.pk)
        return product

    persisted = Product.objects.select_for_update().get(pk=product.pk)
    for field in ("sku", "category", "title", "description", "unit_price", "active", "image_key"):
        setattr(persisted, field, getattr(product, field))
    persisted.full_clean()
    persisted.save()
    return persisted
