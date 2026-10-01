from __future__ import annotations

from collections.abc import Callable
from ipaddress import IPv4Address, IPv6Address, ip_address
from uuid import uuid4

from config.production import parse_networks
from django.conf import settings
from django.db import OperationalError
from django.http import HttpRequest, HttpResponse

from modules.common.api_errors import problem_response

MAX_API_BODY_BYTES = 64 * 1024
IPAddress = IPv4Address | IPv6Address


class TrustedProxyHeadersMiddleware:
    """Honor forwarded client/protocol headers only from explicitly trusted peers."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.trusted_networks = parse_networks(settings.TRUSTED_PROXY_CIDRS)

    def _is_trusted(self, address: IPAddress) -> bool:
        return any(
            address.version == network.version and address in network
            for network in self.trusted_networks
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        peer_value = request.META.get("REMOTE_ADDR", "")
        try:
            peer = ip_address(peer_value)
        except ValueError:
            peer = None

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        if peer is None or not self._is_trusted(peer):
            request.META.pop("HTTP_X_FORWARDED_FOR", None)
            request.META.pop("HTTP_X_FORWARDED_PROTO", None)
            return self.get_response(request)

        forwarded_addresses: list[IPAddress] = []
        try:
            if forwarded_for:
                forwarded_addresses = [
                    ip_address(value.strip()) for value in forwarded_for.split(",")
                ]
        except ValueError:
            request.META.pop("HTTP_X_FORWARDED_FOR", None)
            request.META.pop("HTTP_X_FORWARDED_PROTO", None)
            return self.get_response(request)

        address_chain = [*forwarded_addresses, peer]
        while len(address_chain) > 1 and self._is_trusted(address_chain[-1]):
            address_chain.pop()
        request.META["REMOTE_ADDR"] = str(address_chain[-1])
        request.META.pop("HTTP_X_FORWARDED_FOR", None)

        normalized_proto = forwarded_proto.strip().lower()
        if normalized_proto in {"http", "https"}:
            request.META["HTTP_X_FORWARDED_PROTO"] = normalized_proto
        else:
            request.META.pop("HTTP_X_FORWARDED_PROTO", None)
        return self.get_response(request)


class RequestIdMiddleware:
    """Generate a server-owned request ID and attach it to every response."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = str(uuid4())
        request.META["BLAST_ECOM_REQUEST_ID"] = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class ApiRequestSizeLimitMiddleware:
    """Reject oversized business API bodies before parsers allocate them."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/api/v1/"):
            content_length = request.META.get("CONTENT_LENGTH")
            if content_length:
                try:
                    declared_length = int(content_length)
                except ValueError:
                    return problem_response(
                        request=request,
                        status=400,
                        code="INVALID_CONTENT_LENGTH",
                        detail="Content-Length is invalid.",
                    )
                if declared_length < 0:
                    return problem_response(
                        request=request,
                        status=400,
                        code="INVALID_CONTENT_LENGTH",
                        detail="Content-Length is invalid.",
                    )
                if declared_length > MAX_API_BODY_BYTES:
                    return problem_response(
                        request=request,
                        status=413,
                        code="PAYLOAD_TOO_LARGE",
                        detail="The request body exceeds the 64 KiB limit.",
                    )
        return self.get_response(request)


class DatabaseUnavailableMiddleware:
    """Return a generic temporary-unavailable response for API database outages."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse | None:
        if request.path.startswith("/api/") and isinstance(exception, OperationalError):
            return problem_response(
                request=request,
                status=503,
                code="SERVICE_UNAVAILABLE",
                detail="The service is temporarily unavailable.",
            )
        if request.path.startswith("/admin/") and isinstance(exception, OperationalError):
            return HttpResponse(
                "The service is temporarily unavailable.",
                status=503,
                content_type="text/plain; charset=utf-8",
            )
        return None
