from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from modules.common.serializers import ProblemDetailSerializer
from modules.products.models import Category, Product
from modules.products.selectors import active_categories, active_products
from modules.products.serializers import CategorySerializer, ProductSerializer


class CatalogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_description = "Page number in the paginated result set."
    page_size_query_description = "Number of results to return per page (maximum 100)."


class CategoryListView(generics.ListAPIView[Category]):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    pagination_class = CatalogPagination

    @extend_schema(
        responses={
            200: CategorySerializer(many=True),
            (404, "application/problem+json"): ProblemDetailSerializer,
        }
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Category]:
        return active_categories()


class ProductListView(generics.ListAPIView[Product]):
    permission_classes = (AllowAny,)
    serializer_class = ProductSerializer
    pagination_class = CatalogPagination
    ordering_options = {
        "title": ("title", "id"),
        "-title": ("-title", "id"),
        "price": ("unit_price", "id"),
        "-price": ("-unit_price", "id"),
    }

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category",
                type=UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by category UUID.",
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                location=OpenApiParameter.QUERY,
                enum=list(ordering_options),
                required=False,
                description="Order by title or price; prefixes '-' for descending order.",
            ),
        ],
        responses={
            200: ProductSerializer(many=True),
            (400, "application/problem+json"): ProblemDetailSerializer,
            (404, "application/problem+json"): ProblemDetailSerializer,
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Product]:
        queryset = active_products()
        category_id = self.request.query_params.get("category")
        if category_id:
            try:
                UUID(category_id)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"category": "A valid category UUID is required."}
                ) from exc
            queryset = queryset.filter(category_id=category_id)

        ordering = self.request.query_params.get("ordering", "title")
        try:
            fields = self.ordering_options[ordering]
        except KeyError as exc:
            raise serializers.ValidationError(
                {"ordering": "Use title, -title, price, or -price."}
            ) from exc
        return queryset.order_by(*fields)


class ProductDetailView(generics.RetrieveAPIView[Product]):
    permission_classes = (AllowAny,)
    serializer_class = ProductSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    @extend_schema(
        responses={
            200: ProductSerializer,
            (404, "application/problem+json"): ProblemDetailSerializer,
        }
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Product]:
        return active_products()
