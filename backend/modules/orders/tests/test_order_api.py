from __future__ import annotations

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from rest_framework.test import APIClient

from modules.common.middleware import ApiRequestSizeLimitMiddleware
from modules.inventory.models import StockItem
from modules.inventory.services import adjust_stock
from modules.orders.models import Order
from modules.products.models import Category, Product
from modules.products.services import save_product
from modules.users.models import User

ADDRESS = {
    "recipient": "Ada Example",
    "address_line_1": "1 Fictional Street",
    "address_line_2": "",
    "city": "Madrid",
    "region": "Madrid",
    "postal_code": "28001",
    "country_code": "ES",
}


@pytest.fixture
def shop() -> tuple[User, Product]:
    user = User.objects.create_user("customer@example.test", password="A-long-safe-password-123")
    category = Category.objects.create(slug=f"api-{uuid4().hex[:8]}", name="API demo")
    product = save_product(
        Product(
            sku=f"API-{uuid4().hex[:8]}",
            category=category,
            title="API product",
            unit_price=Decimal("9.95"),
        )
    )
    adjust_stock(product_id=product.pk, actor=user, delta=3, reason="API test stock")
    return user, product


def authenticated_client(user: User) -> tuple[APIClient, str]:
    client = APIClient(enforce_csrf_checks=True)
    token = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
    client.force_login(user)
    return client, token


def order_payload(product: Product, quantity: int = 1) -> dict[str, object]:
    return {
        "items": [
            {
                "product_id": str(product.pk),
                "quantity": quantity,
                "expected_unit_price": "9.95",
            }
        ],
        "delivery_address": ADDRESS,
    }


@pytest.mark.django_db
def test_order_api_requires_session_csrf_and_idempotency_key(shop: tuple[User, Product]) -> None:
    user, product = shop
    anonymous = APIClient(enforce_csrf_checks=True)
    denied = anonymous.post("/api/v1/orders/", order_payload(product), format="json")
    assert denied.status_code == 403
    assert denied.json()["code"] == "AUTH_REQUIRED"

    client, token = authenticated_client(user)
    no_csrf = client.post("/api/v1/orders/", order_payload(product), format="json")
    assert no_csrf.status_code == 403
    assert no_csrf.json()["code"] == "CSRF_FAILED"

    invalid_csrf = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN="not-a-valid-csrf-token",
    )
    assert invalid_csrf.status_code == 403
    assert invalid_csrf.json()["code"] == "CSRF_FAILED"

    missing_key = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert missing_key.status_code == 400
    assert missing_key["Content-Type"] == "application/problem+json"
    assert missing_key.json()["field_errors"][0]["field"] == "Idempotency-Key"
    assert Order.objects.count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=False, REQUIRE_VERIFIED_CUSTOMER_EMAIL=True)
def test_unverified_customer_cannot_create_public_order(shop: tuple[User, Product]) -> None:
    user, product = shop
    client, token = authenticated_client(user)

    response = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )

    assert response.status_code == 403
    assert Order.objects.count() == 0
    stock = StockItem.objects.get(product=product)
    assert (stock.on_hand, stock.reserved) == (3, 0)


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"],
)
def test_order_creation_rejects_untrusted_origin_with_valid_csrf(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    client, token = authenticated_client(user)

    response = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_ORIGIN="http://attacker.example",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_FAILED"
    assert Order.objects.count() == 0
    stock = StockItem.objects.get(product=product)
    assert (stock.on_hand, stock.reserved) == (3, 0)


@pytest.mark.django_db
@override_settings(
    DEBUG=True,
    CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"],
)
def test_order_actions_reject_untrusted_origin_without_changing_order_or_stock(
    shop: tuple[User, Product],
) -> None:
    user, product = shop
    client, token = authenticated_client(user)
    created = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    payment = client.post(
        f"/api/v1/orders/{order_id}/payment/",
        {},
        format="json",
        HTTP_ORIGIN="http://attacker.example",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    cancellation = client.post(
        f"/api/v1/orders/{order_id}/cancel/",
        {},
        format="json",
        HTTP_ORIGIN="http://attacker.example",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )

    assert payment.status_code == cancellation.status_code == 403
    assert payment.json()["code"] == cancellation.json()["code"] == "CSRF_FAILED"
    assert Order.objects.get(pk=order_id).state == Order.State.AWAITING_PAYMENT
    assert not hasattr(Order.objects.get(pk=order_id), "payment_attempt")
    stock = StockItem.objects.get(product=product)
    assert (stock.on_hand, stock.reserved) == (3, 1)


@pytest.mark.django_db
def test_order_create_replay_conflict_and_owner_only_address(shop: tuple[User, Product]) -> None:
    user, product = shop
    client, token = authenticated_client(user)
    key = str(uuid4())
    created = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=key,
    )
    replay = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=key,
    )
    changed = client.post(
        "/api/v1/orders/",
        order_payload(product, quantity=2),
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=key,
    )

    assert created.status_code == replay.status_code == 201
    assert created.json() == replay.json()
    assert created.json()["total"] == "9.95"
    assert "delivery_address" not in created.json()
    assert changed.status_code == 409
    assert changed["Content-Type"] == "application/problem+json"
    assert changed.json()["code"] == "IDEMPOTENCY_CONFLICT"
    assert Order.objects.count() == 1
    detail = client.get(f"/api/v1/orders/{created.json()['id']}/")
    assert detail.status_code == 200
    assert detail.json()["delivery_address"]["recipient"] == ADDRESS["recipient"]


@pytest.mark.django_db
def test_order_list_detail_actions_and_idempotency_are_owner_scoped(
    shop: tuple[User, Product],
) -> None:
    owner, product = shop
    owner_client, owner_token = authenticated_client(owner)
    created = owner_client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=owner_token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    order_id = created.json()["id"]
    other = User.objects.create_user("other@example.test", password="A-long-safe-password-123")
    other_client, other_token = authenticated_client(other)

    listing = other_client.get("/api/v1/orders/")
    detail = other_client.get(f"/api/v1/orders/{order_id}/")
    payment = other_client.post(
        f"/api/v1/orders/{order_id}/payment/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=other_token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    cancellation = other_client.post(
        f"/api/v1/orders/{order_id}/cancel/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=other_token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )

    assert listing.status_code == 200
    assert listing.json()["count"] == 0
    assert detail.status_code == payment.status_code == cancellation.status_code == 404
    assert all(
        response.json()["code"] == "NOT_FOUND" for response in (detail, payment, cancellation)
    )
    assert Order.objects.get(pk=order_id).state == Order.State.AWAITING_PAYMENT


@pytest.mark.django_db
def test_order_actions_reject_client_outcome_and_do_not_leak_non_owner_keys(
    shop: tuple[User, Product],
) -> None:
    owner, product = shop
    client, token = authenticated_client(owner)
    created = client.post(
        "/api/v1/orders/",
        order_payload(product),
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    order_id = created.json()["id"]
    invalid = client.post(
        f"/api/v1/orders/{order_id}/payment/",
        {"outcome": "success"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    result = client.post(
        f"/api/v1/orders/{order_id}/payment/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )

    assert invalid.status_code == 400
    assert result.status_code == 200
    assert result.json()["payment"]["outcome"] == "succeeded"
    assert "card" not in str(result.json()).lower()
    stock = StockItem.objects.get(product=product)
    assert (stock.on_hand, stock.reserved) == (2, 0)


@pytest.mark.django_db
def test_payload_size_limit_and_generated_schema_cover_order_routes() -> None:
    client = APIClient(enforce_csrf_checks=True)
    large = client.post(
        "/api/v1/auth/login/",
        {"padding": "x" * (64 * 1024)},
        format="json",
        HTTP_X_REQUEST_ID="untrusted-id",
    )
    schema = client.get("/api/schema/?format=json").json()

    assert large.status_code == 413
    assert large["Content-Type"] == "application/problem+json"
    assert large.json()["code"] == "PAYLOAD_TOO_LARGE"
    assert large["X-Request-ID"] != "untrusted-id"
    assert "/api/v1/orders/" in schema["paths"]
    assert "/api/v1/orders/{order_id}/payment/" in schema["paths"]
    assert "/api/v1/auth/csrf/" in schema["paths"]
    create = schema["paths"]["/api/v1/orders/"]["post"]
    assert create["responses"]["201"]
    assert {parameter["name"] for parameter in create["parameters"]} >= {
        "X-CSRFToken",
        "Idempotency-Key",
    }
    payment = schema["paths"]["/api/v1/orders/{order_id}/payment/"]["post"]
    assert {parameter["name"] for parameter in payment["parameters"]} >= {
        "X-CSRFToken",
        "Idempotency-Key",
    }
    login = schema["paths"]["/api/v1/auth/login/"]["post"]
    assert any(parameter["name"] == "X-CSRFToken" for parameter in login["parameters"])
    order_list = schema["paths"]["/api/v1/orders/"]["get"]
    assert all(parameter["name"] != "X-CSRFToken" for parameter in order_list["parameters"])
    assert "cookieAuth" in create["security"][0]
    assert "application/problem+json" in create["responses"]["400"]["content"]
    assert "outcome" not in str(create["requestBody"])


@pytest.mark.django_db
def test_negative_content_length_is_rejected() -> None:
    request = RequestFactory().generic("POST", "/api/v1/orders/")
    request.META["CONTENT_LENGTH"] = "-1"
    middleware = ApiRequestSizeLimitMiddleware(lambda request: HttpResponse(status=204))

    response = middleware(request)

    assert response.status_code == 400
    assert json.loads(response.content)["code"] == "INVALID_CONTENT_LENGTH"


@pytest.mark.django_db
def test_unknown_api_route_uses_problem_details() -> None:
    response = APIClient().get("/api/v1/not-a-route/")

    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "NOT_FOUND"
