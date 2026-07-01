"""Tenant Context — async context variable for multi-tenant isolation."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

# Context variables for the current request
_tenant_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("user_id", default=None)
_correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_roles_ctx: ContextVar[list[str]] = ContextVar("roles", default=[])


class TenantContext:
    """Thread/async-safe tenant context using Python contextvars.

    Stores the current tenant, user, and request metadata for the
    duration of a request. Used by repositories and services to
    automatically scope queries and operations.

    Usage:
        # Set in middleware
        TenantContext.set_tenant_id(tenant_uuid)
        TenantContext.set_user_id(user_uuid)

        # Read anywhere in the request lifecycle
        tenant_id = TenantContext.get_tenant_id()
        user_id = TenantContext.get_user_id()
    """

    @staticmethod
    def get_tenant_id() -> uuid.UUID | None:
        """Get the current tenant ID."""
        return _tenant_id_ctx.get()

    @staticmethod
    def get_tenant_id_required() -> uuid.UUID:
        """Get the current tenant ID, raising if not set."""
        tenant_id = _tenant_id_ctx.get()
        if tenant_id is None:
            raise RuntimeError("Tenant context not set. Ensure tenant middleware is configured.")
        return tenant_id

    @staticmethod
    def set_tenant_id(tenant_id: uuid.UUID | None) -> None:
        """Set the current tenant ID."""
        _tenant_id_ctx.set(tenant_id)

    @staticmethod
    def get_user_id() -> uuid.UUID | None:
        """Get the current user ID."""
        return _user_id_ctx.get()

    @staticmethod
    def get_user_id_required() -> uuid.UUID:
        """Get the current user ID, raising if not set."""
        user_id = _user_id_ctx.get()
        if user_id is None:
            raise RuntimeError("User context not set. Ensure auth middleware is configured.")
        return user_id

    @staticmethod
    def set_user_id(user_id: uuid.UUID | None) -> None:
        """Set the current user ID."""
        _user_id_ctx.set(user_id)

    @staticmethod
    def get_correlation_id() -> str | None:
        """Get the current correlation ID."""
        return _correlation_id_ctx.get()

    @staticmethod
    def set_correlation_id(correlation_id: str | None) -> None:
        """Set the current correlation ID."""
        _correlation_id_ctx.set(correlation_id)

    @staticmethod
    def get_roles() -> list[str]:
        """Get the current user's roles."""
        return _roles_ctx.get()

    @staticmethod
    def set_roles(roles: list[str]) -> None:
        """Set the current user's roles."""
        _roles_ctx.set(roles)

    @staticmethod
    def clear() -> None:
        """Clear all context variables."""
        _tenant_id_ctx.set(None)
        _user_id_ctx.set(None)
        _correlation_id_ctx.set(None)
        _roles_ctx.set([])

    @staticmethod
    def to_dict() -> dict[str, Any]:
        """Export context as a dictionary (for logging/propagation)."""
        return {
            "tenant_id": str(_tenant_id_ctx.get()) if _tenant_id_ctx.get() else None,
            "user_id": str(_user_id_ctx.get()) if _user_id_ctx.get() else None,
            "correlation_id": _correlation_id_ctx.get(),
            "roles": _roles_ctx.get(),
        }


class RequestContext(BaseModel):
    """Immutable snapshot of the current request context."""

    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    correlation_id: str | None = None
    roles: list[str] = []
    ip_address: str | None = None
    user_agent: str | None = None

    @classmethod
    def from_context(cls) -> RequestContext:
        """Create a snapshot from the current context variables."""
        return cls(
            tenant_id=TenantContext.get_tenant_id(),
            user_id=TenantContext.get_user_id(),
            correlation_id=TenantContext.get_correlation_id(),
            roles=TenantContext.get_roles(),
        )
