"""Audit Service Controllers."""

import structlog
from fastapi import APIRouter, Depends, Request

from converse_shared.application.dto import ApiResponse
from converse_shared.security.tenant_context import TenantContext

from audit_service.application.dto.audit_dto import LogActionRequest, AuditLogResponse
from audit_service.application.commands.log_action import LogActionCommand
from audit_service.main import mediator  # Global mediator instance

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


@router.post("/log", response_model=ApiResponse[AuditLogResponse])
async def log_action(request: LogActionRequest, req: Request):
    """Log an action performed in the system."""
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        from converse_shared.domain.exceptions import AuthorizationError
        raise AuthorizationError("Tenant ID not found in context.")
        
    user_id = TenantContext.get_user_id()
        
    command = LogActionCommand(
        tenant_id=tenant_id,
        user_id=user_id,
        action=request.action,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        details=request.details,
        ip_address=req.client.host if req.client else None,
    )
    result = await mediator.send(command)
    return ApiResponse.created(data=result.data)
