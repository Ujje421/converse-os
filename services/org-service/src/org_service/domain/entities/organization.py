"""Domain entities for Organization Management."""

from __future__ import annotations

import uuid
from typing import Any

from converse_shared.domain.aggregate_root import AggregateRoot
from converse_shared.domain.base_entity import BaseEntity


class OrganizationMember(BaseEntity):
    """Entity representing a user's membership in an organization."""
    user_id: uuid.UUID
    role: str  # OWNER, ADMIN, MEMBER, VIEWER


class Organization(AggregateRoot):
    """Aggregate root for managing an organization (tenant)."""

    name: str
    slug: str
    billing_plan: str = "FREE"
    is_active: bool = True
    settings: dict[str, Any]
    members: list[OrganizationMember]

    @classmethod
    def create(
        cls,
        name: str,
        slug: str,
        owner_id: uuid.UUID,
    ) -> Organization:
        """Create a new organization."""
        org = cls(
            name=name,
            slug=slug,
            settings={},
            members=[],
        )
        # The creator becomes the owner
        org.add_member(user_id=owner_id, role="OWNER")
        return org

    def add_member(self, user_id: uuid.UUID, role: str) -> None:
        """Add a member to the organization."""
        # Check if already a member
        if any(m.user_id == user_id for m in self.members):
            raise ValueError(f"User {user_id} is already a member")
            
        self.members.append(OrganizationMember(user_id=user_id, role=role))
        self.mark_updated()
        # Could emit OrgMemberAddedEvent

    def remove_member(self, user_id: uuid.UUID) -> None:
        """Remove a member from the organization."""
        # Ensure we don't remove the last owner
        member = next((m for m in self.members if m.user_id == user_id), None)
        if not member:
            return
            
        if member.role == "OWNER":
            owner_count = sum(1 for m in self.members if m.role == "OWNER")
            if owner_count <= 1:
                raise ValueError("Cannot remove the last owner of the organization")
                
        self.members = [m for m in self.members if m.user_id != user_id]
        self.mark_updated()

    def update_settings(self, new_settings: dict[str, Any]) -> None:
        """Update organization settings."""
        self.settings.update(new_settings)
        self.mark_updated()
