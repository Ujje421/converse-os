"""SQLAlchemy implementation of UserProfileRepository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from converse_shared.domain.value_objects import Email

from user_service.domain.entities.user_profile import UserProfile
from user_service.domain.repositories.user_repo import UserProfileRepository
from user_service.infrastructure.persistence.models import UserProfileModel


class SqlUserProfileRepository(UserProfileRepository):
    """SQLAlchemy-based implementation of UserProfileRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, profile: UserProfile) -> None:
        """Save a user profile aggregate to the database."""
        model = await self.session.get(UserProfileModel, profile.id)
        
        if not model:
            # Create new
            model = UserProfileModel(
                id=profile.id,
                email=str(profile.email),
                first_name=profile.first_name,
                last_name=profile.last_name,
                avatar_url=profile.avatar_url,
                timezone=profile.timezone,
                preferences=profile.preferences,
            )
            self.session.add(model)
        else:
            # Update existing
            model.email = str(profile.email)
            model.first_name = profile.first_name
            model.last_name = profile.last_name
            model.avatar_url = profile.avatar_url
            model.timezone = profile.timezone
            model.preferences = profile.preferences
            
        await self.session.flush()

    async def get_by_id(self, user_id: uuid.UUID) -> UserProfile | None:
        """Retrieve profile by user ID."""
        model = await self.session.get(UserProfileModel, user_id)
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> UserProfile | None:
        """Retrieve profile by email address."""
        stmt = select(UserProfileModel).where(UserProfileModel.email == str(email))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: UserProfileModel) -> UserProfile:
        """Map SQLAlchemy model to Domain Entity."""
        entity = UserProfile.reconstitute(
            id=model.id,
            email=Email(model.email),
            first_name=model.first_name,
            last_name=model.last_name,
            avatar_url=model.avatar_url,
            timezone=model.timezone,
            preferences=model.preferences,
        )
        return entity
