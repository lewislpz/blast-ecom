from django.urls import path

from modules.orders.api import OrderCancelView, OrderDetailView, OrderListView, OrderPaymentView

urlpatterns = [
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<uuid:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<uuid:order_id>/payment/", OrderPaymentView.as_view(), name="order-payment"),
    path("orders/<uuid:order_id>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
]
