"""Get User Profile Query."""

import uuid

import structlog

from converse_shared.application.cqrs import Query, QueryHandler
from converse_shared.application.dto import Result
from converse_shared.domain.exceptions import EntityNotFound

from user_service.domain.repositories.user_repo import UserProfileRepository
from user_service.application.dto.user_dto import UserProfileResponse

logger = structlog.get_logger()


class GetProfileQuery(Query[UserProfileResponse]):
    """Query to get a user profile."""
    user_id: uuid.UUID


class GetProfileQueryHandler(QueryHandler[GetProfileQuery, UserProfileResponse]):
    """Handler for getting a user profile."""

    def __init__(self, repo: UserProfileRepository) -> None:
        self.repo = repo

    async def handle(self, query: GetProfileQuery) -> Result[UserProfileResponse]:
        """Process the get profile query."""
        profile = await self.repo.get_by_id(query.user_id)
        if not profile:
            raise EntityNotFound(message="User profile not found")
            
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
