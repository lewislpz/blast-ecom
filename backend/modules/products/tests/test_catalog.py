from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.test import Client, RequestFactory
from rest_framework.test import APIClient

from modules.inventory.models import StockItem
from modules.inventory.services import adjust_stock
from modules.products.admin import ProductAdmin
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User


@pytest.mark.django_db
def test_product_creation_creates_zero_stock_item() -> None:
    category = Category.objects.create(slug="apparel", name="Apparel")
    product = save_product(
        Product(
            sku="TEE-001",
            category=category,
            title="Demo T-shirt",
            unit_price=Decimal("18.50"),
        )
    )

    stock_item = StockItem.objects.get(product=product)
    assert (stock_item.on_hand, stock_item.reserved, stock_item.available) == (0, 0, 0)


@pytest.mark.django_db
def test_catalog_lists_only_active_products_and_categories() -> None:
    active_category = Category.objects.create(slug="active", name="Active")
    inactive_category = Category.objects.create(slug="inactive", name="Inactive", active=False)
    visible = save_product(
        Product(
            sku="VISIBLE-1",
            category=active_category,
            title="Visible product",
            unit_price=Decimal("12.00"),
        )
    )
    hidden_product = save_product(
        Product(
            sku="HIDDEN-1",
            category=active_category,
            title="Hidden product",
            unit_price=Decimal("8.00"),
            active=False,
        )
    )
    category_hidden_product = save_product(
        Product(
            sku="HIDDEN-2",
            category=inactive_category,
            title="Category hidden product",
            unit_price=Decimal("9.00"),
        )
    )
    staff = User.objects.create_user("staff@example.test", is_staff=True)
    adjust_stock(product_id=visible.pk, actor=staff, delta=3, reason="Opening stock")

    client = APIClient()
    categories = client.get("/api/v1/categories/").json()["results"]
    products = client.get("/api/v1/products/").json()["results"]

    assert [category["slug"] for category in categories] == ["active"]
    assert [product["sku"] for product in products] == ["VISIBLE-1"]
    assert products[0]["in_stock"] is True
    assert products[0]["unit_price"] == "12.00"
    assert products[0]["currency"] == "EUR"
    visible_ids = {product["id"] for product in products}
    assert str(hidden_product.pk) not in visible_ids
    assert str(category_hidden_product.pk) not in visible_ids


@pytest.mark.django_db
def test_product_detail_hides_inactive_or_unknown_products() -> None:
    category = Category.objects.create(slug="demo", name="Demo")
    product = save_product(
        Product(
            sku="DEMO-1",
            category=category,
            title="Demo",
            unit_price=Decimal("1.00"),
            active=False,
        )
    )
    client = APIClient()

    assert client.get(f"/api/v1/products/{product.pk}/").status_code == 404
    assert client.get(f"/api/v1/products/{uuid4()}/").status_code == 404


@pytest.mark.django_db
def test_product_api_is_read_only_and_supports_documented_filters() -> None:
    category = Category.objects.create(slug="demo", name="Demo")
    for sku, title, price in (
        ("DEMO-1", "Beta", Decimal("20.00")),
        ("DEMO-2", "Alpha", Decimal("10.00")),
    ):
        save_product(Product(sku=sku, category=category, title=title, unit_price=price))
    client = APIClient()

    response = client.get("/api/v1/products/", {"category": str(category.pk), "ordering": "price"})
    assert response.status_code == 200
    assert [product["sku"] for product in response.json()["results"]] == ["DEMO-2", "DEMO-1"]
    invalid = client.get(
        "/api/v1/products/",
        {"ordering": "secret_field"},
        HTTP_X_REQUEST_ID="client-controlled-id",
    )
    assert invalid.status_code == 400
    assert invalid["Content-Type"] == "application/problem+json"
    assert invalid["X-Request-ID"] == invalid.json()["request_id"]
    assert invalid["X-Request-ID"] != "client-controlled-id"
    assert invalid.json()["code"] == "INVALID_INPUT"
    assert invalid.json()["field_errors"][0]["field"] == "ordering"
    assert client.get("/api/v1/products/", {"category": "not-a-uuid"}).status_code == 400
    assert client.post("/api/v1/products/", {"sku": "FORGED"}).status_code == 405
    assert client.post("/api/v1/categories/", {"slug": "forged"}).status_code == 405


def test_openapi_schema_exposes_catalog_and_problem_details() -> None:
    schema = APIClient().get("/api/schema/?format=json").json()

    products = schema["paths"]["/api/v1/products/"]["get"]
    detail = schema["paths"]["/api/v1/products/{id}/"]["get"]
    assert "200" in products["responses"]
    assert "basicAuth" not in schema["components"]["securitySchemes"]
    assert products["responses"]["400"]["content"]["application/problem+json"]
    assert detail["responses"]["404"]["content"]["application/problem+json"]
    product_page_ref = products["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    product_page = schema["components"]["schemas"][product_page_ref.rsplit("/", 1)[-1]]
    assert product_page["properties"]["results"]["items"]["$ref"] == "#/components/schemas/Product"


@pytest.mark.django_db
def test_catalog_permissions_require_named_staff_grants_and_reject_superusers() -> None:
    factory = RequestFactory()
    admin_model = ProductAdmin(Product, AdminSite())
    staff = User.objects.create_user("staff@example.test", is_staff=True)
    request = factory.get("/admin/products/product/")
    request.user = staff

    assert admin_model.has_add_permission(request) is False
    permission = Permission.objects.get(content_type__app_label="products", codename="add_product")
    staff.user_permissions.add(permission)
    staff = User.objects.get(pk=staff.pk)
    request.user = staff
    assert admin_model.has_add_permission(request) is True

    superuser = User.objects.create_superuser("root@example.test", "temporary-password")
    request.user = superuser
    assert admin_model.has_add_permission(request) is False
    assert admin_model.has_delete_permission(request) is False


@pytest.mark.django_db
def test_admin_product_creation_requires_named_permission_and_initializes_inventory() -> None:
    category = Category.objects.create(slug="admin-demo", name="Admin demo")
    staff = User.objects.create_user("catalog-operator@example.test", is_staff=True)
    client = Client()
    client.force_login(staff)

    assert client.get("/admin/products/product/add/").status_code == 403

    permission = Permission.objects.get(content_type__app_label="products", codename="add_product")
    staff.user_permissions.add(permission)
    client.force_login(User.objects.get(pk=staff.pk))
    response = client.post(
        "/admin/products/product/add/",
        {
            "sku": "ADMIN-1",
            "category": str(category.pk),
            "title": "Admin product",
            "description": "Fictional catalog entry",
            "unit_price": "17.50",
            "active": "on",
            "image_key": "",
        },
    )

    assert response.status_code == 302
    product = Product.objects.get(sku="ADMIN-1")
    assert StockItem.objects.get(product=product).available == 0
