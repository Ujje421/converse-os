"""SQLAlchemy ORM models for Auth Service."""

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from converse_shared.infrastructure.database import BaseModel


class UserCredentialsModel(BaseModel):
    """Database model for user credentials."""

    __tablename__ = "user_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
