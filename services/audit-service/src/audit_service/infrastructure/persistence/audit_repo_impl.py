"""SQLAlchemy implementation of AuditRepository."""

from sqlalchemy.ext.asyncio import AsyncSession

from audit_service.domain.entities.audit_log import AuditLog
from audit_service.domain.repositories.audit_repo import AuditRepository
from audit_service.infrastructure.persistence.models import AuditLogModel


class SqlAuditRepository(AuditRepository):
    """SQLAlchemy-based implementation of AuditRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, log: AuditLog) -> None:
        """Save a new audit log entry."""
        model = AuditLogModel(
            id=log.id,
            tenant_id=log.tenant_id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        self.session.add(model)
        await self.session.flush()
