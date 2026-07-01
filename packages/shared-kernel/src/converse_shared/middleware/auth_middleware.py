"""Authentication extraction middleware."""

import uuid
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from converse_shared.security.tenant_context import TenantContext

logger = structlog.get_logger()

USER_ID_HEADER = "X-User-ID"
USER_ROLES_HEADER = "X-User-Roles"


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Extracts User ID and Roles from headers set by API Gateway.
    
    The API Gateway validates the JWT and passes user details downstream
    via headers. This middleware populates the local TenantContext.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        user_id_str = request.headers.get(USER_ID_HEADER)
        roles_str = request.headers.get(USER_ROLES_HEADER)
        
        if user_id_str:
            try:
                user_id = uuid.UUID(user_id_str)
                TenantContext.set_user_id(user_id)
            except ValueError:
                logger.warning("invalid_user_id_format", header=user_id_str)
                
        if roles_str:
            roles = [r.strip() for r in roles_str.split(",") if r.strip()]
            TenantContext.set_roles(roles)
            
            # Simple hack for decorators since FastAPI Dependency Injection
            # is preferred over middleware for setting auth user state on requests,
            # but we attach a dummy current_user to request.state for `@require_permission`
            class CurrentUser:
                def __init__(self, uid: uuid.UUID, r: list[str]):
                    self.id = uid
                    self.roles = r
            
            if user_id_str and 'user_id' in locals():
                request.state.current_user = CurrentUser(user_id, roles)
        
        response = await call_next(request)
        return response
