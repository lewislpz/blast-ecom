from decimal import Decimal

import pytest
from django.core.management import call_command
from django.test import override_settings

from modules.inventory.models import StockAdjustment, StockItem
from modules.products.models import Product


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_local_catalog_is_idempotent_and_preserves_existing_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BLAST_ECOM_ALLOW_LOCAL_SEED", "true")
    call_command("seed_local_catalog")
    product = Product.objects.get(sku="BLAST-DEMO-001")
    stock = StockItem.objects.get(product=product)
    assert product.category.slug == "blast-ecom-demo"
    assert product.category.name == "Local demo fixtures"
    assert product.unit_price == Decimal("18.50")
    assert stock.on_hand == 5
    assert stock.reserved == 0
    assert StockAdjustment.objects.filter(product=product, delta=5).count() == 1
    adjustment = StockAdjustment.objects.get(product=product)
    assert adjustment.reason == "Initial fictional local demo stock"
    actor = adjustment.actor
    assert actor.is_active is False
    assert actor.has_usable_password() is False
    assert adjustment.actor_id == actor.pk

    product.unit_price = Decimal("21.00")
    product.save(update_fields=["unit_price"])
    stock.on_hand = 3
    stock.save(update_fields=["on_hand"])
    call_command("seed_local_catalog")

    product.refresh_from_db()
    stock.refresh_from_db()
    assert product.unit_price == Decimal("21.00")
    assert stock.on_hand == 3
    assert StockAdjustment.objects.filter(product=product, delta=5).count() == 1


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_seed_local_catalog_is_refused_outside_debug() -> None:
    from django.core.management.base import CommandError

    with pytest.raises(CommandError, match="DEBUG mode"):
        call_command("seed_local_catalog")

    assert Product.objects.count() == 0
