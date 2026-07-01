"""FastAPI Application Factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import make_asgi_app

from converse_shared.config.settings import AppSettings
from converse_shared.infrastructure.health import HealthCheckRegistry
from converse_shared.middleware.correlation_id import CorrelationIdMiddleware
from converse_shared.middleware.error_handler import ErrorHandlerMiddleware
from converse_shared.middleware.request_logging import RequestLoggingMiddleware
from converse_shared.middleware.tenant_middleware import TenantMiddleware
from converse_shared.observability.logging import setup_logging
from converse_shared.observability.tracing import setup_tracing

logger = structlog.get_logger()


def create_app(
    settings: AppSettings,
    health_registry: HealthCheckRegistry,
    lifespan: Callable[[FastAPI], AsyncGenerator[None, None]] | None = None,
    add_metrics_endpoint: bool = True,
) -> FastAPI:
    """Create and configure a standardized FastAPI application.
    
    Args:
        settings: Application settings.
        health_registry: Health check registry.
        lifespan: Optional FastAPI lifespan context manager.
        add_metrics_endpoint: Whether to expose Prometheus /metrics.
        
    Returns:
        Configured FastAPI application.
    """
    
    # Setup Logging
    setup_logging(
        service_name=settings.service_name,
        version=settings.service_version,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    
    # Setup Tracing
    setup_tracing(
        service_name=settings.service_name,
        version=settings.service_version,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        sampling_ratio=settings.otel_traces_sampler_arg,
    )
    
    @asynccontextmanager
    async def default_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # Startup
        logger.info("service_starting", service=settings.service_name)
        if lifespan:
            async with lifespan(app):
                yield
        else:
            yield
        # Shutdown
        logger.info("service_shutting_down", service=settings.service_name)

    # Initialize FastAPI
    app = FastAPI(
        title=f"Converse AI - {settings.service_name.replace('-', ' ').title()}",
        version=settings.service_version,
        description="Converse Enterprise Conversational AI Platform",
        lifespan=default_lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # --- Middlewares (Executed bottom-to-top) ---
    
    # 5. Global Error Handler (Top-level exception catcher)
    app.add_middleware(ErrorHandlerMiddleware)
    
    # 4. Request Logging & Metrics
    app.add_middleware(RequestLoggingMiddleware, service_name=settings.service_name)
    
    # 3. Tenant Context Extraction
    app.add_middleware(TenantMiddleware)
    
    # 2. Correlation ID Propagation
    app.add_middleware(CorrelationIdMiddleware)
    
    # 1. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Usually restricted by Gateway or Config
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # --- Standard Endpoints ---
    
    @app.get("/health", tags=["System"])
    async def health_check():
        """Aggregated health check for Kubernetes liveness/readiness probes."""
        return await health_registry.check_all()
        
    @app.get("/health/live", tags=["System"])
    async def liveness_check():
        """Quick liveness probe."""
        is_live = await health_registry.check_liveness()
        if not is_live:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Service Unhealthy")
        return {"status": "alive"}
        
    @app.get("/health/ready", tags=["System"])
    async def readiness_check():
        """Deep readiness probe."""
        is_ready = await health_registry.check_readiness()
        if not is_ready:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Service Not Ready")
        return {"status": "ready"}

    # Expose Prometheus Metrics endpoint
    if add_metrics_endpoint:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    return app
