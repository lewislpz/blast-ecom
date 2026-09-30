from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.common.exceptions import DomainOperationError
from modules.common.serializers import ProblemDetailSerializer
from modules.orders.models import Order
from modules.orders.serializers import (
    CreateOrderRequestSerializer,
    OrderDetailResponseSerializer,
    OrderOperationResponseSerializer,
    PaymentOperationResponseSerializer,
)
from modules.orders.services import (
    cancel_order,
    create_order,
    get_owned_order,
    owned_orders,
    simulate_payment,
)
from modules.users.models import User

CSRF_HEADER = OpenApiParameter(
    name="X-CSRFToken",
    type=str,
    location="header",
    required=True,
    description="Django CSRF token obtained from /api/v1/auth/csrf/.",
)
IDEMPOTENCY_HEADER = OpenApiParameter(
    name="Idempotency-Key",
    type=UUID,
    location="header",
    required=True,
    description="A UUIDv4 key scoped to this customer and operation.",
)


class IsActiveCustomer(BasePermission):
    message = "Customer access is required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return bool(
            user.is_authenticated and user.is_active and not user.is_staff and not user.is_superuser
        )


class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderListPageSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = OrderOperationResponseSerializer(many=True)


def _customer(request: Request) -> User:
    if not isinstance(request.user, User):
        raise DomainOperationError(status_code=403, code="AUTH_REQUIRED")
    return request.user


def _idempotency_key(request: Request) -> UUID:
    raw = request.headers.get("Idempotency-Key")
    try:
        key = UUID(raw or "")
    except ValueError as exc:
        raise serializers.ValidationError(
            {"Idempotency-Key": "A UUIDv4 Idempotency-Key is required."}
        ) from exc
    if key.version != 4:
        raise serializers.ValidationError(
            {"Idempotency-Key": "A UUIDv4 Idempotency-Key is required."}
        )
    return key


def _result_response(result: Any) -> Response:
    if result.status >= 400:
        code = result.body.get("code", "REQUEST_ERROR")
        raise DomainOperationError(status_code=result.status, code=str(code))
    return Response(result.body, status=result.status)


def _require_empty_body(request: Request) -> None:
    if request.data not in ({}, None):
        raise serializers.ValidationError(
            {"non_field_errors": "This action does not accept a body."}
        )


class OrderListView(APIView):
    permission_classes = (IsAuthenticated, IsActiveCustomer)
    pagination_class = OrderPagination

    @extend_schema(
        operation_id="orders_list",
        parameters=[
            OpenApiParameter(
                name="state", type=str, enum=[value for value, _ in Order.State.choices]
            ),
            OpenApiParameter(name="page", type=int),
            OpenApiParameter(name="page_size", type=int),
        ],
        responses={
            200: OrderListPageSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        queryset: QuerySet[Order] = owned_orders(user=_customer(request))
        state = request.query_params.get("state")
        if state:
            valid_states = {value for value, _ in Order.State.choices}
            if state not in valid_states:
                raise serializers.ValidationError({"state": "Use a supported order state."})
            queryset = queryset.filter(state=state)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is None:
            raise RuntimeError("Order pagination did not produce a page.")
        return paginator.get_paginated_response(
            OrderOperationResponseSerializer(page, many=True).data
        )

    @extend_schema(
        operation_id="orders_create",
        parameters=[CSRF_HEADER, IDEMPOTENCY_HEADER],
        request=CreateOrderRequestSerializer,
        responses={
            201: OrderOperationResponseSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (409, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = CreateOrderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        items = [
            {
                "product_id": str(line["product_id"]),
                "quantity": line["quantity"],
                "expected_unit_price": line["expected_unit_price"],
            }
            for line in data["items"]
        ]
        result = create_order(
            user=_customer(request),
            idempotency_key=_idempotency_key(request),
            items=items,
            address=data["delivery_address"],
        )
        return _result_response(result)


class OrderDetailView(APIView):
    permission_classes = (IsAuthenticated, IsActiveCustomer)

    @extend_schema(
        operation_id="orders_retrieve",
        responses={
            200: OrderDetailResponseSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (404, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def get(self, request: Request, order_id: UUID) -> Response:
        order = get_owned_order(user=_customer(request), order_id=order_id)
        if order is None:
            raise DomainOperationError(status_code=404, code="NOT_FOUND")
        return Response(OrderDetailResponseSerializer(order).data)


class OrderPaymentView(APIView):
    permission_classes = (IsAuthenticated, IsActiveCustomer)

    @extend_schema(
        operation_id="orders_simulate_payment",
        request=None,
        parameters=[
            CSRF_HEADER,
            IDEMPOTENCY_HEADER,
        ],
        responses={
            200: PaymentOperationResponseSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (404, "application/problem+json"): ProblemDetailSerializer,
            (409, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request, order_id: UUID) -> Response:
        _require_empty_body(request)
        result = simulate_payment(
            user=_customer(request),
            order_id=order_id,
            idempotency_key=_idempotency_key(request),
        )
        return _result_response(result)


class OrderCancelView(APIView):
    permission_classes = (IsAuthenticated, IsActiveCustomer)

    @extend_schema(
        operation_id="orders_cancel",
        request=None,
        parameters=[
            CSRF_HEADER,
            IDEMPOTENCY_HEADER,
        ],
        responses={
            200: OrderOperationResponseSerializer,
            (400, "application/problem+json"): ProblemDetailSerializer,
            (403, "application/problem+json"): ProblemDetailSerializer,
            (404, "application/problem+json"): ProblemDetailSerializer,
            (409, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def post(self, request: Request, order_id: UUID) -> Response:
        _require_empty_body(request)
        result = cancel_order(
            user=_customer(request),
            order_id=order_id,
            idempotency_key=_idempotency_key(request),
        )
        return _result_response(result)
