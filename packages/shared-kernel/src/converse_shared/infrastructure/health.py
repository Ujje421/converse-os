"""Health check infrastructure — composable health checks for all dependencies."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger()


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealthResult:
    """Result of a single component health check."""

    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class OverallHealthResult:
    """Aggregated health status of the service."""

    status: HealthStatus
    service_name: str
    version: str
    components: list[ComponentHealthResult] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "service": self.service_name,
            "version": self.version,
            "timestamp": self.timestamp,
            "components": {
                c.name: {
                    "status": c.status.value,
                    "latency_ms": round(c.latency_ms, 2),
                    "message": c.message,
                    **c.details,
                }
                for c in self.components
            },
        }


HealthCheckFn = Callable[[], Coroutine[Any, Any, bool]]


class HealthCheckRegistry:
    """Registry of health check functions for service dependencies.

    Usage:
        registry = HealthCheckRegistry(service_name="auth-service", version="0.1.0")
        registry.register("postgres", check_postgres)
        registry.register("redis", check_redis)

        result = await registry.check_all()
    """

    def __init__(self, service_name: str, version: str = "0.0.0") -> None:
        self._service_name = service_name
        self._version = version
        self._checks: dict[str, HealthCheckFn] = {}

    def register(self, name: str, check_fn: HealthCheckFn) -> None:
        """Register a health check function for a component."""
        self._checks[name] = check_fn
        logger.debug("health_check_registered", component=name)

    async def check_all(self) -> OverallHealthResult:
        """Run all registered health checks and return aggregated results."""
        from datetime import UTC, datetime

        components: list[ComponentHealthResult] = []
        overall_status = HealthStatus.HEALTHY

        for name, check_fn in self._checks.items():
            start = time.monotonic()
            try:
                is_healthy = await check_fn()
                latency = (time.monotonic() - start) * 1000

                status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
                components.append(
                    ComponentHealthResult(
                        name=name,
                        status=status,
                        latency_ms=latency,
                        message="OK" if is_healthy else "Check failed",
                    )
                )

                if not is_healthy:
                    overall_status = HealthStatus.UNHEALTHY

            except Exception as e:
                latency = (time.monotonic() - start) * 1000
                components.append(
                    ComponentHealthResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        message=str(e),
                    )
                )
                overall_status = HealthStatus.UNHEALTHY
                logger.error("health_check_error", component=name, error=str(e))

        return OverallHealthResult(
            status=overall_status,
            service_name=self._service_name,
            version=self._version,
            components=components,
            timestamp=datetime.now(UTC).isoformat(),
        )

    async def check_readiness(self) -> bool:
        """Quick readiness check — all components must be healthy."""
        result = await self.check_all()
        return result.status == HealthStatus.HEALTHY

    async def check_liveness(self) -> bool:
        """Liveness check — the service process is running."""
        return True
