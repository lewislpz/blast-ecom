import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.inventory.services import adjust_stock, ensure_stock_item
from modules.products.models import Category, Product
from modules.users.models import User


class Command(BaseCommand):
    help = "Create the fictional local demo category and product without resetting existing data."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        del args, options
        database_host = settings.DATABASES["default"].get("HOST", "")
        is_local_database = database_host in {"", "localhost", "127.0.0.1", "::1"}
        if (
            not settings.DEBUG
            or not is_local_database
            or os.environ.get("BLAST_ECOM_ALLOW_LOCAL_SEED") != "true"
        ):
            raise CommandError(
                "seed_local_catalog requires DEBUG mode, a local database and "
                "BLAST_ECOM_ALLOW_LOCAL_SEED=true."
            )

        category, _ = Category.objects.get_or_create(
            slug="blast-ecom-demo",
            defaults={"name": "Local demo fixtures", "active": True},
        )
        product, created = Product.objects.get_or_create(
            sku="BLAST-DEMO-001",
            defaults={
                "category": category,
                "title": "Taza de demostración Blast",
                "description": "Producto ficticio para probar el flujo local.",
                "unit_price": Decimal("18.50"),
                "active": True,
                "image_key": "ceramic-mug",
            },
        )
        ensure_stock_item(product_id=product.pk)
        if created:
            actor, actor_created = User.objects.get_or_create(
                email=f"seed-actor-{product.pk}@blast-ecom.invalid",
                defaults={"is_active": False, "is_staff": False, "is_superuser": False},
            )
            if actor_created:
                actor.set_unusable_password()
                actor.save(update_fields=["password"])
            if (
                actor.has_usable_password()
                or actor.is_active
                or actor.is_staff
                or actor.is_superuser
            ):
                raise CommandError("Refusing to reuse an active or credentialed seed audit actor.")
            adjust_stock(
                product_id=product.pk,
                actor=actor,
                delta=5,
                reason="Initial fictional local demo stock",
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Local demo product "
                f"{'created' if created else 'already existed'}: {product.sku} ({product.pk})."
            )
        )
