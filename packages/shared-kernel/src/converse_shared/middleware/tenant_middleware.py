"""Tenant extraction middleware."""

import uuid
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from converse_shared.security.tenant_context import TenantContext

logger = structlog.get_logger()

TENANT_ID_HEADER = "X-Tenant-ID"


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts tenant ID from headers and sets it in the TenantContext.
    
    Usually the API Gateway passes this header after resolving the tenant
    from the user's JWT or custom domain.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        tenant_id_str = request.headers.get(TENANT_ID_HEADER)
        
        if tenant_id_str:
            try:
                tenant_id = uuid.UUID(tenant_id_str)
                TenantContext.set_tenant_id(tenant_id)
            except ValueError:
                logger.warning("invalid_tenant_id_format", header=tenant_id_str)
        
        response = await call_next(request)
        return response
