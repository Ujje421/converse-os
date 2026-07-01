"""DTOs — Data Transfer Objects for API responses and inter-layer communication."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseDTO(BaseModel):
    """Base DTO with common serialization configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response envelope.

    All API endpoints return responses wrapped in this envelope for
    consistent client consumption.

    Attributes:
        success: Whether the request succeeded.
        data: The response payload.
        error: Error details if the request failed.
        meta: Additional metadata (pagination, timing, etc.).
        request_id: Unique request identifier for support/debugging.
    """

    success: bool = True
    data: Any = None
    error: ErrorDetail | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None

    @classmethod
    def ok(cls, data: Any = None, **meta: Any) -> ApiResponse:
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def created(cls, data: Any = None, **meta: Any) -> ApiResponse:
        return cls(success=True, data=data, meta={**meta, "status": "created"})

    @classmethod
    def fail(
        cls,
        error_code: str,
        message: str,
        details: list[FieldError] | None = None,
        status_code: int = 400,
    ) -> ApiResponse:
        return cls(
            success=False,
            error=ErrorDetail(
                code=error_code,
                message=message,
                details=details or [],
                status_code=status_code,
            ),
        )


class ErrorDetail(BaseModel):
    """Structured error information for API responses."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: list[FieldError] = Field(default_factory=list, description="Field-level errors")
    status_code: int = Field(default=400, description="HTTP status code")


class FieldError(BaseModel):
    """Field-level validation error."""

    field: str
    message: str
    code: str = "invalid"


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with metadata."""

    items: list[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False

    @classmethod
    def from_paginated_result(cls, result: Any) -> PaginatedResponse:
        """Create from a PaginatedResult domain object."""
        return cls(
            items=result.items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_previous=result.has_previous,
        )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = ""
    service: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    checks: dict[str, ComponentHealth] = Field(default_factory=dict)


class ComponentHealth(BaseModel):
    """Individual component health status."""

    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AuditContext(BaseModel):
    """Context for audit logging."""

    user_id: uuid.UUID | None = None
    tenant_id: uuid.UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    correlation_id: str | None = None
    action: str = ""
    resource_type: str = ""
    resource_id: str | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
