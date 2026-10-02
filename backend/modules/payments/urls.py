from django.urls import path

from modules.payments.api import stripe_webhook

urlpatterns = [path("payments/stripe/webhook/", stripe_webhook, name="stripe-webhook")]
