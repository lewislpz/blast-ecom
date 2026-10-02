"""Authenticated-provider webhook boundary for Stripe sandbox events."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from modules.orders.services import process_provider_event
from modules.payments.models import PaymentAttempt, ProviderEvent
from modules.payments.stripe_provider import StripeProviderError

STRIPE_AUTHORIZATION_EVENT = "payment_intent.amount_capturable_updated"


def _response(status: int) -> HttpResponse:
    return HttpResponse(status=status)


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    if settings.PAYMENT_PROVIDER != "stripe_sandbox":
        return _response(404)
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, UnicodeDecodeError, stripe.SignatureVerificationError):
        return JsonResponse({"code": "INVALID_PROVIDER_SIGNATURE"}, status=400)

    event_payload = event.to_dict()
    event_id = str(event_payload.get("id", ""))
    event_type = str(event_payload.get("type", ""))
    if not event_id or len(event_id) > 255:
        return JsonResponse({"code": "INVALID_PROVIDER_EVENT"}, status=400)
    if event_type != STRIPE_AUTHORIZATION_EVENT:
        return _response(204)

    data = event_payload.get("data")
    provider_object = data.get("object") if isinstance(data, Mapping) else None
    if not isinstance(provider_object, Mapping):
        return JsonResponse({"code": "INVALID_PROVIDER_EVENT"}, status=400)
    payment_intent_id = str(provider_object.get("id", ""))
    metadata = provider_object.get("metadata")
    if not payment_intent_id or not isinstance(metadata, Mapping):
        return JsonResponse({"code": "INVALID_PROVIDER_EVENT"}, status=400)
    try:
        attempt_id = UUID(str(metadata.get("payment_attempt_id", "")))
        order_id = UUID(str(metadata.get("order_id", "")))
        amount = int(provider_object.get("amount", -1))
        amount_capturable = int(provider_object.get("amount_capturable", -1))
    except (TypeError, ValueError):
        return JsonResponse({"code": "INVALID_PROVIDER_EVENT"}, status=400)
    if amount < 0 or amount_capturable < 0:
        return JsonResponse({"code": "INVALID_PROVIDER_EVENT"}, status=400)
    currency = str(provider_object.get("currency", ""))
    if len(currency) != 3:
        return JsonResponse({"code": "INVALID_PROVIDER_EVENT"}, status=400)

    attempt = PaymentAttempt.objects.filter(
        pk=attempt_id,
        order_id=order_id,
        provider=PaymentAttempt.Provider.STRIPE,
    ).first()
    if attempt is None:
        # Valid events unrelated to a current local attempt are acknowledged without effects.
        return _response(204)

    defaults: dict[str, Any] = {
        "event_type": event_type,
        "payment_intent_id": payment_intent_id,
        "payment_attempt": attempt,
        "amount": amount,
        "amount_capturable": amount_capturable,
        "currency": currency.lower(),
    }
    try:
        with transaction.atomic():
            receipt, created = ProviderEvent.objects.get_or_create(
                provider_event_id=event_id,
                defaults=defaults,
            )
    except IntegrityError:
        # A concurrent webhook transaction may have inserted this event ID.
        recovered_receipt = ProviderEvent.objects.filter(provider_event_id=event_id).first()
        if recovered_receipt is None:
            return _response(503)
        receipt = recovered_receipt
        created = False

    if not created and (
        receipt.payment_attempt_id != attempt.pk
        or receipt.payment_intent_id != payment_intent_id
        or receipt.amount != amount
        or receipt.amount_capturable != amount_capturable
        or receipt.currency != currency.lower()
    ):
        return JsonResponse({"code": "PROVIDER_EVENT_CONFLICT"}, status=400)
    if receipt.status == ProviderEvent.Status.PROCESSED:
        return _response(204)

    try:
        process_provider_event(event_id=event_id)
    except (stripe.StripeError, StripeProviderError):
        # Non-2xx asks Stripe to redeliver; the minimal receipt remains retryable.
        return _response(503)
    return _response(204)
