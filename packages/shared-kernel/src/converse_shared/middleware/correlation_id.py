"""Correlation ID middleware for tracking requests across microservices."""

import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from converse_shared.security.tenant_context import TenantContext

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to extract or generate a Correlation ID for every request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            
        TenantContext.set_correlation_id(correlation_id)
        
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        
        return response
