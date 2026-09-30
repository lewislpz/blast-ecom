from django.urls import path

from modules.products.api import CategoryListView, ProductDetailView, ProductListView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<uuid:id>/", ProductDetailView.as_view(), name="product-detail"),
]
