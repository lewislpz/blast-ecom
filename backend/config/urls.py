"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework.permissions import AllowAny

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("modules.users.urls")),
    path("api/v1/", include("modules.orders.urls")),
    path("api/v1/", include("modules.products.urls")),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name="openapi-schema",
    ),
]

handler404 = "modules.common.api_errors.api_not_found"
handler500 = "modules.common.api_errors.api_server_error"
