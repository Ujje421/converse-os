"""Domain entities for Audit Service."""

from __future__ import annotations

import uuid
from typing import Any
from datetime import datetime, UTC

from converse_shared.domain.base_entity import BaseEntity


class AuditLog(BaseEntity):
    """Entity representing an immutable audit log entry.
    Note: Intentionally not an Aggregate Root because audit logs do not emit 
    domain events and are not updated after creation.
    """

    tenant_id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    ip_address: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        tenant_id: uuid.UUID,
        action: str,
        resource_type: str,
        user_id: uuid.UUID | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        return cls(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            created_at=datetime.now(UTC)
        )
