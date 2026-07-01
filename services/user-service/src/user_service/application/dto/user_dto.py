"""User Service DTOs."""

from pydantic import BaseModel, EmailStr
from typing import Any


class UserProfileResponse(BaseModel):
    """Response DTO for user profile."""
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    avatar_url: str | None
    timezone: str
    preferences: dict[str, Any]


class UpdateProfileRequest(BaseModel):
    """Request DTO for updating a user profile."""
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    timezone: str | None = None
    
    
class UpdatePreferencesRequest(BaseModel):
    """Request DTO for updating user preferences."""
    preferences: dict[str, Any]
