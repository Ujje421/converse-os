"""OpenTelemetry tracing configuration."""

from __future__ import annotations

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

logger = structlog.get_logger()


def setup_tracing(
    service_name: str,
    version: str,
    otlp_endpoint: str | None = None,
    sampling_ratio: float = 1.0,
    enable_instrumentation: bool = True,
) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Name of the service.
        version: Version of the service.
        otlp_endpoint: OTLP gRPC endpoint (e.g., http://localhost:4317).
        sampling_ratio: Trace sampling ratio (0.0 to 1.0).
        enable_instrumentation: Whether to auto-instrument libraries.
    """
    if not otlp_endpoint:
        logger.info("tracing_disabled", reason="no otlp endpoint configured")
        return

    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "service.version": version,
        }
    )

    sampler = TraceIdRatioBased(sampling_ratio)
    provider = TracerProvider(resource=resource, sampler=sampler)
    
    # Configure OTLP Exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    trace.set_tracer_provider(provider)
    logger.info("tracing_configured", endpoint=otlp_endpoint, sampling_ratio=sampling_ratio)

    if enable_instrumentation:
        try:
            # Note: FastAPI instrumentation happens on the app instance later
            # SQLAlchemyInstrumentor().instrument(engine=...) happens on engine creation
            RedisInstrumentor().instrument()
            HTTPXClientInstrumentor().instrument()
            logger.info("tracing_auto_instrumentation_enabled")
        except Exception as e:
            logger.warning("tracing_instrumentation_failed", error=str(e))


def get_tracer(module_name: str) -> trace.Tracer:
    """Get a tracer for the current module."""
    return trace.get_tracer(module_name)
