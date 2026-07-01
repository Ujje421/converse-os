"""SQLAlchemy ORM models for User Service."""

import uuid

from sqlalchemy import String, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from converse_shared.infrastructure.database import BaseModel


class UserProfileModel(BaseModel):
    """Database model for user profile."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
