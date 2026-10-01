from __future__ import annotations

import hashlib
import hmac
import ipaddress
from datetime import datetime
from typing import Any, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from rest_framework.exceptions import ParseError, UnsupportedMediaType
from rest_framework.throttling import BaseThrottle

from modules.users.models import AuthAttemptBucket


def _bucket_key(*, scope: str, dimension: str, identity: str) -> str:
    message = f"{scope}\0{dimension}\0{identity}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def _increment_bucket(*, key: str, window_seconds: int, limit: int) -> tuple[int, int]:
    """Atomically increment or start a fixed window using the PostgreSQL clock."""
    if connection.vendor != "postgresql":
        raise ImproperlyConfigured("Authentication throttling requires PostgreSQL.")
    if window_seconds < 1 or limit < 1:
        raise ImproperlyConfigured("Authentication throttle limits and windows must be positive.")

    table = connection.ops.quote_name(AuthAttemptBucket._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            WITH db_clock AS (SELECT clock_timestamp() AS now)
            INSERT INTO {table} AS bucket
                (bucket_key, window_started_at, attempts, expires_at)
            SELECT %s, db_clock.now, 1,
                   db_clock.now + (%s * INTERVAL '1 second')
            FROM db_clock
            ON CONFLICT (bucket_key) DO UPDATE SET
                window_started_at = CASE
                    WHEN bucket.expires_at <= (SELECT now FROM db_clock)
                    THEN EXCLUDED.window_started_at ELSE bucket.window_started_at
                END,
                attempts = CASE
                    WHEN bucket.expires_at <= (SELECT now FROM db_clock)
                    THEN 1 ELSE LEAST(bucket.attempts + 1, %s)
                END,
                expires_at = CASE
                    WHEN bucket.expires_at <= (SELECT now FROM db_clock)
                    THEN EXCLUDED.expires_at ELSE bucket.expires_at
                END
            RETURNING attempts,
                GREATEST(0, CEIL(EXTRACT(EPOCH FROM (expires_at - clock_timestamp()))))::integer
            """,
            [key, window_seconds, limit + 1],
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Authentication throttle counter returned no result.")
    return int(row[0]), int(row[1])


def normalize_client_source(remote_addr: Any) -> str:
    if not isinstance(remote_addr, str) or not remote_addr:
        return "unknown"
    try:
        source = ipaddress.ip_address(remote_addr).compressed
    except ValueError:
        source = "unknown"
    return source


def normalize_identity(identity: Any) -> str | None:
    if isinstance(identity, str):
        normalized = identity.strip().lower()
        if 0 < len(normalized) <= 254:
            return normalized
    return None


def _request_identity(request: Any) -> str | None:
    try:
        email = request.data.get("email")
    except (AttributeError, ParseError, TypeError, UnsupportedMediaType):
        email = None
    return normalize_identity(email)


def consume_auth_attempts(*, scope: str, source: str, identity: str | None) -> tuple[bool, int]:
    policies = settings.AUTH_ATTEMPT_LIMITS.get(scope)
    if policies is None:
        raise ImproperlyConfigured(f"Missing authentication throttle policy for {scope!r}.")

    candidates = [("source", source)]
    if identity is not None:
        candidates.append(("identity_source", f"{source}\0{identity}"))

    allowed = True
    retry_after = 0
    for dimension, identity_value in candidates:
        policy = policies.get(dimension)
        if policy is None:
            if dimension == "source":
                raise ImproperlyConfigured(f"Missing source throttle policy for {scope!r}.")
            continue
        limit = int(policy["limit"])
        if limit < 1:
            raise ImproperlyConfigured("Authentication throttle limits must be positive.")
        attempts, bucket_retry_after = _increment_bucket(
            key=_bucket_key(scope=scope, dimension=dimension, identity=identity_value),
            window_seconds=int(policy["window_seconds"]),
            limit=limit,
        )
        if attempts > limit:
            allowed = False
            retry_after = max(retry_after, bucket_retry_after)
    return allowed, retry_after


class AuthenticationAttemptThrottle(BaseThrottle):
    """Shared PostgreSQL limits for anonymous authentication endpoints."""

    def __init__(self) -> None:
        self.retry_after = 0

    def allow_request(self, request: Any, view: Any) -> bool:
        scope = getattr(view, "throttle_scope", None)
        if scope is None:
            return True
        if not isinstance(scope, str):
            raise ImproperlyConfigured("Authentication throttle scopes must be strings.")
        allowed, self.retry_after = consume_auth_attempts(
            scope=scope,
            source=normalize_client_source(request.META.get("REMOTE_ADDR")),
            identity=_request_identity(request),
        )
        return allowed

    def wait(self) -> float | None:
        return float(max(1, self.retry_after)) if self.retry_after else None


def delete_expired_auth_attempt_buckets(*, limit: int = 100) -> int:
    if not 1 <= limit <= 1000:
        raise ValueError("Cleanup batch limit must be between 1 and 1000.")
    with connection.cursor() as cursor:
        cursor.execute("SELECT clock_timestamp()")
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Database clock query returned no result.")
    cutoff = cast(datetime, row[0])
    expired_keys = list(
        AuthAttemptBucket.objects.filter(expires_at__lte=cutoff)
        .order_by("expires_at", "bucket_key")
        .values_list("bucket_key", flat=True)[:limit]
    )
    if not expired_keys:
        return 0
    deleted, _ = AuthAttemptBucket.objects.filter(
        bucket_key__in=expired_keys, expires_at__lte=cutoff
    ).delete()
    return deleted
