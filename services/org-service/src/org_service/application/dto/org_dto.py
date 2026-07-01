"""Organization Service DTOs."""

from pydantic import BaseModel, constr
from typing import Any


class CreateOrgRequest(BaseModel):
    """Request DTO for creating an organization."""
    name: constr(min_length=2, max_length=255) # type: ignore
    slug: constr(min_length=2, max_length=255, pattern=r'^[a-z0-9-]+$') # type: ignore


class OrgMemberResponse(BaseModel):
    """Response DTO for organization member."""
    user_id: str
    role: str


class OrganizationResponse(BaseModel):
    """Response DTO for organization."""
    id: str
    name: str
    slug: str
    billing_plan: str
    is_active: bool
    settings: dict[str, Any]
    members: list[OrgMemberResponse]
