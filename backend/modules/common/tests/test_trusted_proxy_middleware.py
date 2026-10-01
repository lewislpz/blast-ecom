from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings

from modules.common.middleware import TrustedProxyHeadersMiddleware


def request_through_middleware(
    remote_addr: str, forwarded_for: str, forwarded_proto: str
) -> HttpRequest:
    request = RequestFactory().get(
        "/health/ready/",
        HTTP_X_FORWARDED_FOR=forwarded_for,
        HTTP_X_FORWARDED_PROTO=forwarded_proto,
    )
    request.META["REMOTE_ADDR"] = remote_addr

    def inspect(received: HttpRequest) -> HttpResponse:
        return HttpResponse("ok")

    TrustedProxyHeadersMiddleware(inspect)(request)
    return request


@override_settings(TRUSTED_PROXY_CIDRS=())
def test_untrusted_client_cannot_spoof_forwarded_ip_or_https() -> None:
    request = request_through_middleware("198.51.100.20", "203.0.113.8", "https")

    assert request.META["REMOTE_ADDR"] == "198.51.100.20"
    assert "HTTP_X_FORWARDED_FOR" not in request.META
    assert "HTTP_X_FORWARDED_PROTO" not in request.META


@override_settings(TRUSTED_PROXY_CIDRS=("10.0.0.0/8",))
def test_trusted_proxy_uses_rightmost_untrusted_address_and_https() -> None:
    request = request_through_middleware(
        "10.0.0.2", "198.51.100.99, 203.0.113.10, 10.0.0.1", "https"
    )

    assert request.META["REMOTE_ADDR"] == "203.0.113.10"
    assert request.META["HTTP_X_FORWARDED_PROTO"] == "https"


@override_settings(TRUSTED_PROXY_CIDRS=("10.0.0.0/8",))
def test_trusted_proxy_invalid_forwarded_chain_is_ignored() -> None:
    request = request_through_middleware("10.0.0.2", "not-an-ip", "https,http")

    assert request.META["REMOTE_ADDR"] == "10.0.0.2"
    assert "HTTP_X_FORWARDED_FOR" not in request.META
    assert "HTTP_X_FORWARDED_PROTO" not in request.META


@override_settings(TRUSTED_PROXY_CIDRS=("10.0.0.0/8",))
def test_untrusted_direct_peer_cannot_use_valid_looking_chain() -> None:
    request = request_through_middleware("198.51.100.20", "203.0.113.10", "https")

    assert request.META["REMOTE_ADDR"] == "198.51.100.20"
    assert "HTTP_X_FORWARDED_FOR" not in request.META
    assert "HTTP_X_FORWARDED_PROTO" not in request.META
