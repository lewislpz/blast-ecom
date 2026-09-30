from unittest.mock import patch

import pytest
from django.db import OperationalError
from django.test import Client


@pytest.mark.django_db
def test_readiness_reports_database_connectivity_without_internal_details() -> None:
    response = Client().get("/health/ready/")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.django_db
def test_readiness_returns_safe_unavailable_response_when_database_fails() -> None:
    with patch("modules.common.health.connection.cursor", side_effect=OperationalError):
        response = Client().get("/health/ready/")

    assert response.status_code == 503
    assert response.json() == {
        "type": "about:blank",
        "title": "Service Unavailable",
        "status": 503,
        "detail": "The service is temporarily unavailable.",
        "code": "SERVICE_UNAVAILABLE",
        "request_id": response["X-Request-ID"],
    }


@pytest.mark.django_db
def test_api_mutation_returns_safe_problem_when_database_fails() -> None:
    from modules.users.api import RegisterView

    with patch.object(
        RegisterView, "post", side_effect=OperationalError("private database detail")
    ):
        response = Client().post(
            "/api/v1/auth/register/",
            data='{"email":"demo@example.test","password":"not-a-real-password"}',
            content_type="application/json",
        )

    assert response.status_code == 503
    assert response["Content-Type"].startswith("application/problem+json")
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "private database detail" not in response.content.decode()
