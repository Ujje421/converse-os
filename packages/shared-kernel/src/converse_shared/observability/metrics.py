"""Prometheus metrics configuration and standard platform metrics."""

from __future__ import annotations

import time
from typing import Any, Callable

from prometheus_client import Counter, Gauge, Histogram, Info, Summary


class MetricsRegistry:
    """Registry for application-level Prometheus metrics."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self.labels = ["service", "tenant_id", "endpoint", "method", "status"]
        
        # Standard HTTP Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            self.labels,
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            self.labels,
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests currently being processed",
            ["service", "endpoint", "method"],
        )
        
        # Database Metrics
        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["service", "tenant_id", "operation", "table"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )
        self.db_errors_total = Counter(
            "db_errors_total",
            "Total database errors",
            ["service", "tenant_id", "operation", "table", "error_type"],
        )
        
        # Cache Metrics
        self.cache_operations_total = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["service", "tenant_id", "operation", "hit"],
        )
        
        # Messaging / Event Metrics
        self.events_published_total = Counter(
            "events_published_total",
            "Total domain events published",
            ["service", "tenant_id", "event_type", "destination"],
        )
        self.events_consumed_total = Counter(
            "events_consumed_total",
            "Total domain events consumed",
            ["service", "tenant_id", "event_type", "status"],
        )
        
        # Service Info
        self.service_info = Info("service_info", "Service information", ["service"])

    def record_http_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration: float,
        tenant_id: str = "none",
    ) -> None:
        """Record HTTP request metrics."""
        labels = [self.service_name, tenant_id, endpoint, method, str(status)]
        self.http_requests_total.labels(*labels).inc()
        self.http_request_duration_seconds.labels(*labels).observe(duration)

    def record_db_query(
        self,
        operation: str,
        table: str,
        duration: float,
        tenant_id: str = "none",
    ) -> None:
        """Record Database query metrics."""
        self.db_query_duration_seconds.labels(
            self.service_name, tenant_id, operation, table
        ).observe(duration)

    def record_cache_operation(
        self,
        operation: str,
        hit: bool,
        tenant_id: str = "none",
    ) -> None:
        """Record Cache operation metrics."""
        self.cache_operations_total.labels(
            self.service_name, tenant_id, operation, str(hit).lower()
        ).inc()

    def record_event_published(
        self,
        event_type: str,
        destination: str,
        tenant_id: str = "none",
    ) -> None:
        """Record event publishing metrics."""
        self.events_published_total.labels(
            self.service_name, tenant_id, event_type, destination
        ).inc()


# Global metrics registry instance (initialized per service)
_metrics_registry: MetricsRegistry | None = None


def get_metrics_registry(service_name: str | None = None) -> MetricsRegistry:
    """Get or create the global metrics registry."""
    global _metrics_registry
    if _metrics_registry is None:
        if service_name is None:
            service_name = "unknown"
        _metrics_registry = MetricsRegistry(service_name)
    return _metrics_registry
