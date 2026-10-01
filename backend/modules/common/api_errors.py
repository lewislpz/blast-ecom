from __future__ import annotations

from typing import Any
from uuid import uuid4

from django.http import JsonResponse
from django.views.defaults import page_not_found, server_error
from rest_framework.exceptions import ErrorDetail, NotAuthenticated, PermissionDenied, Throttled
from rest_framework.response import Response
from rest_framework.views import exception_handler

STATUS_TITLES = {
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    429: "Too Many Requests",
    413: "Content Too Large",
    500: "Internal Server Error",
    503: "Service Unavailable",
}
STATUS_CODES = {
    400: "INVALID_INPUT",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    500: "INTERNAL_ERROR",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}


def problem_response(*, request: Any, status: int, code: str, detail: str) -> JsonResponse:
    request_id = _request_id(request) or str(uuid4())
    response = JsonResponse(
        {
            "type": "about:blank",
            "title": STATUS_TITLES.get(status, "Request Error"),
            "status": status,
            "detail": detail,
            "code": code,
            "request_id": request_id,
        },
        status=status,
        content_type="application/problem+json",
    )
    response["X-Request-ID"] = request_id
    return response


def _request_id(request: Any) -> str | None:
    metadata = getattr(request, "META", {})
    return metadata.get("BLAST_ECOM_REQUEST_ID")


def csrf_failure(request: Any, reason: str = "") -> JsonResponse:
    """Use a generic API-safe response; never disclose Django's CSRF failure detail."""
    del reason
    return problem_response(
        request=request,
        status=403,
        code="CSRF_FAILED",
        detail="CSRF verification failed.",
    )


def api_not_found(request: Any, exception: Exception) -> Any:
    if request.path.startswith("/api/"):
        return problem_response(
            request=request,
            status=404,
            code="NOT_FOUND",
            detail="The requested resource was not found.",
        )
    return page_not_found(request, exception)


def api_server_error(request: Any) -> Any:
    if request.path.startswith("/api/"):
        return problem_response(
            request=request,
            status=500,
            code="INTERNAL_ERROR",
            detail="The request could not be completed.",
        )
    return server_error(request)


def _flatten_errors(data: Any, prefix: str = "") -> list[dict[str, str]]:
    if isinstance(data, dict):
        flattened: list[dict[str, str]] = []
        for field, value in data.items():
            nested_field = f"{prefix}.{field}" if prefix else str(field)
            flattened.extend(_flatten_errors(value, nested_field))
        return flattened
    if isinstance(data, list):
        flattened = []
        for value in data:
            flattened.extend(_flatten_errors(value, prefix))
        return flattened
    if isinstance(data, ErrorDetail):
        return [
            {
                "field": prefix,
                "code": str(data.code).upper(),
                "message": str(data),
            }
        ]
    return [{"field": prefix, "code": "INVALID", "message": str(data)}]


def problem_detail_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    status = response.status_code
    data = response.data
    request = context.get("request")
    request_id = _request_id(request) or str(uuid4())
    field_errors: list[dict[str, str]] = []

    if isinstance(exc, NotAuthenticated):
        detail = "Authentication is required."
        error_code = "AUTH_REQUIRED"
    elif isinstance(exc, Throttled):
        detail = "Too many requests. Try again later."
        error_code = "RATE_LIMITED"
    elif (
        isinstance(exc, PermissionDenied)
        and isinstance(data, dict)
        and str(data.get("detail", "")).startswith("CSRF Failed:")
    ):
        detail = "CSRF verification failed."
        error_code = "CSRF_FAILED"
    elif isinstance(data, dict) and "detail" in data:
        detail = str(data["detail"])
        error_code = str(getattr(data["detail"], "code", STATUS_CODES.get(status, "REQUEST_ERROR")))
    else:
        detail = "The request contains invalid fields."
        field_errors = _flatten_errors(data)
        error_code = STATUS_CODES.get(status, "INVALID_INPUT")

    problem: dict[str, Any] = {
        "type": "about:blank",
        "title": STATUS_TITLES.get(status, "Request Error"),
        "status": status,
        "detail": detail,
        "code": error_code.upper(),
        "request_id": request_id,
    }
    if field_errors:
        problem["field_errors"] = field_errors

    response.data = problem
    response.content_type = "application/problem+json"
    response["X-Request-ID"] = request_id
    return response
