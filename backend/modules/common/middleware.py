from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from modules.common.api_errors import problem_response

MAX_API_BODY_BYTES = 64 * 1024


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
