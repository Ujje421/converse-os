"""Log Action Command."""

import uuid
import structlog
from typing import Any

from converse_shared.application.cqrs import Command, CommandHandler
from converse_shared.application.dto import Result
from converse_shared.infrastructure.unit_of_work import UnitOfWork

from audit_service.domain.entities.audit_log import AuditLog
from audit_service.domain.repositories.audit_repo import AuditRepository
from audit_service.application.dto.audit_dto import AuditLogResponse

logger = structlog.get_logger()


class LogActionCommand(Command[AuditLogResponse]):
    """Command to log a user action."""
    tenant_id: uuid.UUID
    action: str
    resource_type: str
    user_id: uuid.UUID | None = None
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None


class LogActionCommandHandler(CommandHandler[LogActionCommand, AuditLogResponse]):
    """Handler for logging an action."""

    def __init__(
        self,
        uow: UnitOfWork,
        repo: AuditRepository,
    ) -> None:
        self.uow = uow
        self.repo = repo

    async def handle(self, command: LogActionCommand) -> Result[AuditLogResponse]:
        """Process the log action command."""
        async with self.uow:
            log_entry = AuditLog.create(
                tenant_id=command.tenant_id,
                action=command.action,
                resource_type=command.resource_type,
                user_id=command.user_id,
                resource_id=command.resource_id,
                details=command.details,
                ip_address=command.ip_address,
            )
            
            await self.repo.save(log_entry)
            # Not an aggregate root, so we don't register it for events
            
            logger.info(
                "action_logged", 
                action=command.action, 
                resource_type=command.resource_type, 
                tenant_id=str(command.tenant_id)
            )
            
            response = AuditLogResponse(
                id=str(log_entry.id),
                tenant_id=str(log_entry.tenant_id),
                user_id=str(log_entry.user_id) if log_entry.user_id else None,
                action=log_entry.action,
                resource_type=log_entry.resource_type,
                resource_id=log_entry.resource_id,
                details=log_entry.details,
                ip_address=log_entry.ip_address,
                created_at=log_entry.created_at,
            )

            return Result.ok(response)
