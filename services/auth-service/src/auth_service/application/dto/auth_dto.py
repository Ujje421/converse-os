"""Auth Service DTOs."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request DTO for user login."""
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    """Request DTO for user registration."""
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    """Response DTO for tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
