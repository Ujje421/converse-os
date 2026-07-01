"""Create Organization Command."""

import uuid

import structlog

from converse_shared.application.cqrs import Command, CommandHandler
from converse_shared.application.dto import Result
from converse_shared.domain.exceptions import EntityAlreadyExists
from converse_shared.infrastructure.unit_of_work import UnitOfWork

from org_service.domain.entities.organization import Organization
from org_service.domain.repositories.org_repo import OrganizationRepository
from org_service.domain.events.org_events import OrganizationCreatedEvent
from org_service.application.dto.org_dto import OrganizationResponse, OrgMemberResponse

logger = structlog.get_logger()


class CreateOrgCommand(Command[OrganizationResponse]):
    """Command to create a new organization."""
    name: str
    slug: str
    owner_id: uuid.UUID


class CreateOrgCommandHandler(CommandHandler[CreateOrgCommand, OrganizationResponse]):
    """Handler for creating an organization."""

    def __init__(
        self,
        uow: UnitOfWork,
        repo: OrganizationRepository,
    ) -> None:
        self.uow = uow
        self.repo = repo

    async def handle(self, command: CreateOrgCommand) -> Result[OrganizationResponse]:
        """Process the create organization command."""
        async with self.uow:
            # Check for slug uniqueness
            existing = await self.repo.get_by_slug(command.slug)
            if existing:
                raise EntityAlreadyExists(message=f"Organization with slug '{command.slug}' already exists")
                
            org = Organization.create(
                name=command.name,
                slug=command.slug,
                owner_id=command.owner_id,
            )
            
            org.add_domain_event(
                OrganizationCreatedEvent(
                    org_id=org.id,
                    name=org.name,
                    owner_id=command.owner_id,
                )
            )

            await self.repo.save(org)
            self.uow.register_aggregate(org)
            
            logger.info("organization_created", org_id=str(org.id), slug=org.slug)
            
            members = [
                OrgMemberResponse(user_id=str(m.user_id), role=m.role)
                for m in org.members
            ]
            
            response = OrganizationResponse(
                id=str(org.id),
                name=org.name,
                slug=org.slug,
                billing_plan=org.billing_plan,
                is_active=org.is_active,
                settings=org.settings,
                members=members,
            )

            return Result.ok(response)
