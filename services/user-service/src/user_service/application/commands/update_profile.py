"""Update User Profile Command."""

import uuid

import structlog

from converse_shared.application.cqrs import Command, CommandHandler
from converse_shared.application.dto import Result
from converse_shared.domain.exceptions import EntityNotFound
from converse_shared.infrastructure.unit_of_work import UnitOfWork

from user_service.domain.entities.user_profile import UserProfile
from user_service.domain.repositories.user_repo import UserProfileRepository
from user_service.domain.events.user_events import UserProfileUpdatedEvent
from user_service.application.dto.user_dto import UserProfileResponse

logger = structlog.get_logger()


class UpdateProfileCommand(Command[UserProfileResponse]):
    """Command to update user profile information."""
    user_id: uuid.UUID
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    timezone: str | None = None


class UpdateProfileCommandHandler(CommandHandler[UpdateProfileCommand, UserProfileResponse]):
    """Handler for updating a user profile."""

    def __init__(
        self,
        uow: UnitOfWork,
        repo: UserProfileRepository,
    ) -> None:
        self.uow = uow
        self.repo = repo

    async def handle(self, command: UpdateProfileCommand) -> Result[UserProfileResponse]:
        """Process the update profile command."""
        async with self.uow:
            profile = await self.repo.get_by_id(command.user_id)
            if not profile:
                raise EntityNotFound(message="User profile not found")
                
            profile.update_profile(
                first_name=command.first_name,
                last_name=command.last_name,
                avatar_url=command.avatar_url,
                timezone=command.timezone,
            )
            
            profile.add_domain_event(
                UserProfileUpdatedEvent(user_id=profile.id)
            )

            await self.repo.save(profile)
            self.uow.register_aggregate(profile)
            
            logger.info("user_profile_updated", user_id=str(profile.id))
            
            response = UserProfileResponse(
                id=str(profile.id),
                email=str(profile.email),
                first_name=profile.first_name,
                last_name=profile.last_name,
                avatar_url=profile.avatar_url,
                timezone=profile.timezone,
                preferences=profile.preferences,
            )

            return Result.ok(response)
