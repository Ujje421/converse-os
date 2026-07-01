"""SQLAlchemy implementation of OrganizationRepository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from org_service.domain.entities.organization import Organization, OrganizationMember
from org_service.domain.repositories.org_repo import OrganizationRepository
from org_service.infrastructure.persistence.models import OrganizationModel, OrganizationMemberModel


class SqlOrganizationRepository(OrganizationRepository):
    """SQLAlchemy-based implementation of OrganizationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, org: Organization) -> None:
        """Save an organization aggregate to the database."""
        model = await self.session.get(OrganizationModel, org.id)
        
        if not model:
            # Create new
            model = OrganizationModel(
                id=org.id,
                name=org.name,
                slug=org.slug,
                billing_plan=org.billing_plan,
                is_active=org.is_active,
                settings=org.settings,
            )
            for member in org.members:
                model.members.append(
                    OrganizationMemberModel(
                        id=member.id,
                        user_id=member.user_id,
                        role=member.role,
                    )
                )
            self.session.add(model)
        else:
            # Update existing
            model.name = org.name
            model.slug = org.slug
            model.billing_plan = org.billing_plan
            model.is_active = org.is_active
            model.settings = org.settings
            
            # Sync members (basic implementation - assumes full replacement or updates)
            # A more robust approach would compute diffs
            model.members.clear()
            for member in org.members:
                model.members.append(
                    OrganizationMemberModel(
                        id=member.id,
                        user_id=member.user_id,
                        role=member.role,
                    )
                )
            
        await self.session.flush()

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        """Retrieve organization by ID."""
        model = await self.session.get(OrganizationModel, org_id)
        return self._to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Retrieve organization by slug."""
        stmt = select(OrganizationModel).where(OrganizationModel.slug == slug)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: OrganizationModel) -> Organization:
        """Map SQLAlchemy model to Domain Entity."""
        members = [
            OrganizationMember.reconstitute(
                id=m.id,
                user_id=m.user_id,
                role=m.role,
            ) for m in model.members
        ]
        
        entity = Organization.reconstitute(
            id=model.id,
            name=model.name,
            slug=model.slug,
            billing_plan=model.billing_plan,
            is_active=model.is_active,
            settings=model.settings,
            members=members,
        )
        return entity
