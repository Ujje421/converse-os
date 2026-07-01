"""Request logging and metrics middleware."""

import time
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from converse_shared.observability.metrics import get_metrics_registry
from converse_shared.security.tenant_context import TenantContext

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs HTTP requests and records Prometheus metrics."""

    def __init__(self, app, service_name: str) -> None:
        super().__init__(app)
        self.service_name = service_name
        self.metrics = get_metrics_registry(service_name)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.monotonic()
        
        # Don't log health checks verbosely
        is_health = request.url.path in ("/health", "/metrics")
        
        if not is_health:
            logger.info(
                "request_started",
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else None,
            )

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.monotonic() - start_time
            tenant_id = str(TenantContext.get_tenant_id() or "none")
            
            # Record metrics
            self.metrics.record_http_request(
                endpoint=request.url.path,
                method=request.method,
                status=status_code,
                duration=duration,
                tenant_id=tenant_id,
            )
            
            if not is_health or status_code >= 400:
                logger.info(
                    "request_finished",
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    duration_ms=round(duration * 1000, 2),
                )
                
        return response
