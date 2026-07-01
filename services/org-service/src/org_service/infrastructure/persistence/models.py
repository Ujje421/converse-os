"""SQLAlchemy ORM models for Organization Service."""

import uuid

from sqlalchemy import String, JSON, Uuid, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from converse_shared.infrastructure.database import BaseModel


class OrganizationModel(BaseModel):
    """Database model for organization."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    billing_plan: Mapped[str] = mapped_column(String(50), default="FREE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    members: Mapped[list["OrganizationMemberModel"]] = relationship(
        back_populates="organization", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class OrganizationMemberModel(BaseModel):
    """Database model for organization members."""

    __tablename__ = "organization_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    organization: Mapped["OrganizationModel"] = relationship(back_populates="members")
