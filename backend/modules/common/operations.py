from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

from django.db import IntegrityError, connection, transaction

from modules.common.models import IdempotencyRecord
from modules.users.models import User


@dataclass(frozen=True)
class OperationResult:
    status: int
    body: dict[str, Any]
    replayed: bool = False


def database_now() -> datetime:
    """Return fresh PostgreSQL wall-clock time after any preceding row-lock wait."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT clock_timestamp()")
        value = cursor.fetchone()
    if value is None:
        raise RuntimeError("Database clock query returned no result.")
    return cast(datetime, value[0])


def delete_expired_idempotency_records(*, limit: int = 100) -> int:
    if not 1 <= limit <= 1000:
        raise ValueError("Cleanup batch limit must be between 1 and 1000.")
    expired_ids = list(
        IdempotencyRecord.objects.filter(expires_at__lte=database_now())
        .order_by("expires_at", "id")
        .values_list("id", flat=True)[:limit]
    )
    if not expired_ids:
        return 0
    deleted, _ = IdempotencyRecord.objects.filter(id__in=expired_ids).delete()
    return deleted


def fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def execute_idempotent(
    *,
    user: User,
    operation: str,
    key: UUID,
    payload: Mapping[str, Any],
    execute: Callable[[], OperationResult],
    authorize_replay: Callable[[], bool] | None = None,
) -> OperationResult:
    """Serialize an operation by scoped UUID key and persist its result atomically."""
    if key.version != 4:
        return OperationResult(400, {"code": "INVALID_IDEMPOTENCY_KEY"})
    digest = fingerprint(payload)
    with transaction.atomic():
        now = database_now()
        scope = {"user": user, "operation": operation, "key": key}
        record = IdempotencyRecord.objects.select_for_update().filter(**scope).first()

        if record is not None and record.expires_at <= now:
            record.delete()
            record = None

        if record is None:
            try:
                with transaction.atomic():
                    record = IdempotencyRecord.objects.create(
                        **scope,
                        request_hash=digest,
                        expires_at=now + timedelta(hours=24),
                    )
            except IntegrityError:
                # A concurrent request inserted the same scope. The savepoint above
                # keeps this transaction usable so the committed row can be locked.
                record = IdempotencyRecord.objects.select_for_update().get(**scope)
                if record.expires_at <= database_now():
                    record.delete()
                    return execute_idempotent(
                        user=user,
                        operation=operation,
                        key=key,
                        payload=payload,
                        execute=execute,
                    )
                if record.request_hash != digest:
                    return OperationResult(409, {"code": "IDEMPOTENCY_CONFLICT"})
                if record.response_status is None or record.response_body is None:
                    raise RuntimeError("Committed idempotency record has no result.") from None
                if authorize_replay is not None and not authorize_replay():
                    return OperationResult(404, {"code": "NOT_FOUND"})
                return OperationResult(record.response_status, record.response_body, replayed=True)

        if record.request_hash != digest:
            return OperationResult(409, {"code": "IDEMPOTENCY_CONFLICT"})
        if record.response_status is not None and record.response_body is not None:
            if authorize_replay is not None and not authorize_replay():
                return OperationResult(404, {"code": "NOT_FOUND"})
            return OperationResult(record.response_status, record.response_body, replayed=True)
        result = execute()
        record.response_status = result.status
        record.response_body = result.body
        record.save(update_fields=["response_status", "response_body"])
        return result
