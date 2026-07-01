"""User Service Controllers."""

import structlog
from fastapi import APIRouter, Depends, Request

from converse_shared.application.dto import ApiResponse
from converse_shared.security.tenant_context import TenantContext

from user_service.application.dto.user_dto import UpdateProfileRequest, UserProfileResponse
from user_service.application.commands.update_profile import UpdateProfileCommand
from user_service.application.queries.get_profile import GetProfileQuery
from user_service.main import mediator  # Global mediator instance

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse[UserProfileResponse])
async def get_my_profile():
    """Get the profile of the currently authenticated user."""
    user_id = TenantContext.get_user_id()
    if not user_id:
        from converse_shared.domain.exceptions import AuthorizationError
        raise AuthorizationError("User ID not found in context")
        
    query = GetProfileQuery(user_id=user_id)
    result = await mediator.send(query)
    return ApiResponse.ok(data=result.data)


@router.patch("/me", response_model=ApiResponse[UserProfileResponse])
async def update_my_profile(request: UpdateProfileRequest):
    """Update the profile of the currently authenticated user."""
    user_id = TenantContext.get_user_id()
    if not user_id:
        from converse_shared.domain.exceptions import AuthorizationError
        raise AuthorizationError("User ID not found in context")
        
    command = UpdateProfileCommand(
        user_id=user_id,
        first_name=request.first_name,
        last_name=request.last_name,
        avatar_url=request.avatar_url,
        timezone=request.timezone,
    )
    result = await mediator.send(command)
    return ApiResponse.ok(data=result.data)
