"""Domain exceptions — structured error types for the domain layer."""

from __future__ import annotations

import uuid
from typing import Any


class DomainException(Exception):
    """Base exception for all domain-level errors.

    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code for API responses.
        details: Additional context for debugging.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "DOMAIN_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFound(DomainException):
    """Raised when a requested entity does not exist."""

    def __init__(
        self,
        entity_type: str,
        entity_id: uuid.UUID | str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            error_code="ENTITY_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": str(entity_id), **(details or {})},
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class EntityAlreadyExists(DomainException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(
        self,
        entity_type: str,
        conflict_field: str,
        conflict_value: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"{entity_type} with {conflict_field}='{conflict_value}' already exists",
            error_code="ENTITY_ALREADY_EXISTS",
            details={
                "entity_type": entity_type,
                "conflict_field": conflict_field,
                "conflict_value": conflict_value,
                **(details or {}),
            },
        )


class BusinessRuleViolation(DomainException):
    """Raised when a business rule is violated."""

    def __init__(
        self,
        rule: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule, **(details or {})},
        )
        self.rule = rule


class ConcurrencyConflict(DomainException):
    """Raised when an optimistic concurrency conflict is detected."""

    def __init__(
        self,
        entity_type: str,
        entity_id: uuid.UUID | str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Concurrency conflict on {entity_type} with id '{entity_id}'",
            error_code="CONCURRENCY_CONFLICT",
            details={"entity_type": entity_type, "entity_id": str(entity_id), **(details or {})},
        )


class AuthorizationError(DomainException):
    """Raised when a user lacks permission for an operation."""

    def __init__(
        self,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Not authorized to {action} on {resource}",
            error_code="AUTHORIZATION_ERROR",
            details={"action": action, "resource": resource, **(details or {})},
        )


class TenantAccessDenied(DomainException):
    """Raised when cross-tenant access is attempted."""

    def __init__(
        self,
        tenant_id: uuid.UUID | str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message="Access denied: tenant isolation violation",
            error_code="TENANT_ACCESS_DENIED",
            details={"requested_tenant_id": str(tenant_id), **(details or {})},
        )


class ValidationError(DomainException):
    """Raised when input validation fails at the domain level."""

    def __init__(
        self,
        field: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Validation error on '{field}': {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
        )


class RateLimitExceeded(DomainException):
    """Raised when a rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window_seconds}s",
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "limit": limit,
                "window_seconds": window_seconds,
                "retry_after": retry_after,
                **(details or {}),
            },
        )
        self.retry_after = retry_after


class ExternalServiceError(DomainException):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"External service '{service_name}' error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service_name": service_name,
                "status_code": status_code,
                **(details or {}),
            },
        )
