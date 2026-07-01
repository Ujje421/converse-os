"""Org Service Controllers."""

import structlog
from fastapi import APIRouter, Depends, Request

from converse_shared.application.dto import ApiResponse
from converse_shared.security.tenant_context import TenantContext

from org_service.application.dto.org_dto import CreateOrgRequest, OrganizationResponse
from org_service.application.commands.create_org import CreateOrgCommand
from org_service.main import mediator  # Global mediator instance

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/orgs", tags=["Organizations"])


@router.post("", response_model=ApiResponse[OrganizationResponse])
async def create_organization(request: CreateOrgRequest):
    """Create a new organization."""
    user_id = TenantContext.get_user_id()
    if not user_id:
        from converse_shared.domain.exceptions import AuthorizationError
        raise AuthorizationError("User ID not found in context. Must be authenticated to create an org.")
        
    command = CreateOrgCommand(
        name=request.name,
        slug=request.slug,
        owner_id=user_id,
    )
    result = await mediator.send(command)
    return ApiResponse.created(data=result.data)
