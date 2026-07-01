"""Base entity with identity, timestamps, and soft-delete support."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """Base entity providing identity, audit timestamps, and soft-delete.

    All domain entities inherit from this. Uses Pydantic v2 for validation
    and serialization while remaining persistence-agnostic.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique entity identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Creation timestamp (UTC)")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update timestamp (UTC)")
    is_deleted: bool = Field(default=False, description="Soft-delete flag")
    deleted_at: datetime | None = Field(default=None, description="Deletion timestamp (UTC)")

    def mark_updated(self) -> None:
        """Update the `updated_at` timestamp to current UTC time."""
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """Mark the entity as soft-deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
        self.mark_updated()

    def restore(self) -> None:
        """Restore a soft-deleted entity."""
        self.is_deleted = False
        self.deleted_at = None
        self.mark_updated()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
