from django.db import OperationalError, connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from modules.common.api_errors import problem_response


@require_GET
def readiness(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError:
        return problem_response(
            request=request,
            status=503,
            code="SERVICE_UNAVAILABLE",
            detail="The service is temporarily unavailable.",
        )
    return JsonResponse({"status": "ready"})
