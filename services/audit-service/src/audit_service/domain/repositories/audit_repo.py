"""Repository interface for Audit Logs."""

from typing import Protocol

from audit_service.domain.entities.audit_log import AuditLog


class AuditRepository(Protocol):
    """Interface for writing audit logs to persistence."""
    
    async def save(self, log: AuditLog) -> None:
        """Save a new audit log entry."""
        ...
