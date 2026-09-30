from uuid import UUID

from modules.common.models import AuditEntry
from modules.users.models import User


def record_audit(
    *, actor: User | None, action: str, target_id: UUID, metadata: dict[str, str]
) -> AuditEntry:
    """Append a sanitized business audit entry through its owning module."""
    return AuditEntry.objects.create(
        actor=actor, action=action, target_id=target_id, metadata=metadata
    )
