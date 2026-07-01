"""Audit Service DTOs."""

from datetime import datetime
from pydantic import BaseModel
from typing import Any


class LogActionRequest(BaseModel):
    """Request DTO for logging an action."""
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] | None = None


class AuditLogResponse(BaseModel):
    """Response DTO for audit log."""
    id: str
    tenant_id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    ip_address: str | None
    created_at: datetime
