"""SQLAlchemy implementation of UserCredentialsRepository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from converse_shared.domain.value_objects import Email

from auth_service.domain.entities.user_credentials import UserCredentials
from auth_service.domain.value_objects.password import PasswordHash
from auth_service.domain.repositories.credentials_repo import UserCredentialsRepository
from auth_service.infrastructure.persistence.models import UserCredentialsModel


class SqlUserCredentialsRepository(UserCredentialsRepository):
    """SQLAlchemy-based implementation of UserCredentialsRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, credentials: UserCredentials) -> None:
        """Save a user credentials aggregate to the database."""
        model = await self.session.get(UserCredentialsModel, credentials.user_id)
        
        if not model:
            # Create new
            model = UserCredentialsModel(
                user_id=credentials.user_id,
                email=str(credentials.email),
                password_hash=credentials.password_hash.value if credentials.password_hash else None,
                is_active=credentials.is_active,
                is_email_verified=credentials.is_email_verified,
                last_login_at=credentials.last_login_at,
                failed_login_attempts=credentials.failed_login_attempts,
                locked_until=credentials.locked_until,
            )
            self.session.add(model)
        else:
            # Update existing
            model.email = str(credentials.email)
            model.password_hash = credentials.password_hash.value if credentials.password_hash else None
            model.is_active = credentials.is_active
            model.is_email_verified = credentials.is_email_verified
            model.last_login_at = credentials.last_login_at
            model.failed_login_attempts = credentials.failed_login_attempts
            model.locked_until = credentials.locked_until
            
        await self.session.flush()
        # Events will be dispatched by Unit of Work

    async def get_by_id(self, user_id: uuid.UUID) -> UserCredentials | None:
        """Retrieve credentials by user ID."""
        model = await self.session.get(UserCredentialsModel, user_id)
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> UserCredentials | None:
        """Retrieve credentials by email address."""
        stmt = select(UserCredentialsModel).where(UserCredentialsModel.email == str(email))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: UserCredentialsModel) -> UserCredentials:
        """Map SQLAlchemy model to Domain Entity."""
        entity = UserCredentials.reconstitute(
            user_id=model.user_id,
            email=Email(model.email),
            password_hash=PasswordHash(value=model.password_hash) if model.password_hash else None,
            is_active=model.is_active,
            is_email_verified=model.is_email_verified,
            last_login_at=model.last_login_at,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
        )
        return entity
