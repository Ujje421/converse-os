"""Structured JSON logging with tenant context and correlation IDs."""

from __future__ import annotations

import logging
import sys
from typing import Any, MutableMapping

import structlog
from structlog.types import EventDict, Processor

from converse_shared.security.tenant_context import TenantContext


def add_context_vars(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add context variables (tenant, user, correlation id) to every log line."""
    
    # Add correlation ID if present
    correlation_id = TenantContext.get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id

    # Add tenant ID if present
    tenant_id = TenantContext.get_tenant_id()
    if tenant_id:
        event_dict["tenant_id"] = str(tenant_id)

    # Add user ID if present
    user_id = TenantContext.get_user_id()
    if user_id:
        event_dict["user_id"] = str(user_id)

    return event_dict


def setup_logging(
    service_name: str,
    version: str,
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """Configure structlog and standard logging for the application.

    Should be called once at application startup.

    Args:
        service_name: Name of the microservice.
        version: Version of the microservice.
        log_level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        log_format: "json" or "console"
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_context_vars,
    ]

    # Add service context to every log
    structlog.contextvars.bind_contextvars(
        service=service_name,
        version=version,
    )

    if log_format.lower() == "json":
        processor = structlog.processors.JSONRenderer()
    else:
        processor = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            processor,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Fastapi/uvicorn root logger
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers.clear()
        _logger.propagate = True
