"""Converse AI - API Gateway"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response

from converse_shared.fastapi import create_app
from converse_shared.infrastructure.health import HealthCheckRegistry
from converse_shared.infrastructure.cache import CacheManager
from converse_shared.middleware.rate_limiter import RateLimiterMiddleware

from api_gateway.config.settings import settings
from api_gateway.proxy import forward_request, http_client

logger = structlog.get_logger()

# --- Infrastructure Setup ---

cache_manager = CacheManager(
    redis_url=settings.redis_url,
    key_prefix="converse:gateway",
)

# --- Health Checks ---

health_registry = HealthCheckRegistry(
    service_name=settings.service_name,
    version=settings.service_version,
)
health_registry.register("redis", cache_manager.health_check)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("gateway_initializing")
    await cache_manager.initialize()
    
    yield
    
    logger.info("gateway_shutting_down")
    await cache_manager.close()
    await http_client.aclose()


# --- Application Factory ---

app = create_app(
    settings=settings,
    health_registry=health_registry,
    lifespan=lifespan,
    # Gateway specific configuration
    add_metrics_endpoint=True,
)

# Add Global Rate Limiter at the Gateway Level
app.add_middleware(
    RateLimiterMiddleware, 
    cache=cache_manager,
    default_limit=200, # Max 200 req per minute per IP globally
    window_seconds=60
)


# --- Routing & Reverse Proxy ---

# Route Map: Path Prefix -> Downstream Service URL
ROUTE_MAP = {
    "/api/v1/auth": settings.auth_service_url,
    "/api/v1/users": settings.user_service_url,
    "/api/v1/orgs": settings.org_service_url,
    "/api/v1/agents": settings.agent_service_url,
    "/api/v1/audit": settings.audit_service_url,
}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_catch_all(request: Request, path: str):
    """Catch-all route to proxy requests to appropriate downstream microservice."""
    
    request_path = request.url.path
    
    # Exclude gateway's own routes
    if request_path in ("/docs", "/redoc", "/openapi.json", "/health", "/health/live", "/health/ready", "/metrics"):
        # Let FastAPI handle these
        return None 
        
    # Find matching prefix
    target_url = None
    for prefix, downstream_url in ROUTE_MAP.items():
        if request_path.startswith(prefix):
            target_url = downstream_url
            break
            
    if not target_url:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Gateway JWT validation logic could be injected here
    # 1. Check Authorization header
    # 2. Decode JWT with public key (from shared-kernel JWTHandler)
    # 3. Add X-User-ID and X-Tenant-ID headers for downstream
    # For now, we trust the auth service handles its own, but gateway would typically do it.
    
    return await forward_request(request, target_url)
