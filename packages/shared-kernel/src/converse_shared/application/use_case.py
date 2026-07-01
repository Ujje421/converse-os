"""Use Case base class — application-layer business logic orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import structlog

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")

logger = structlog.get_logger()


class UseCase(ABC, Generic[TInput, TOutput]):
    """Abstract base class for application use cases.

    Use cases orchestrate domain logic by coordinating entities,
    repositories, and domain services. They represent a single
    application-level business operation.

    The lifecycle is: validate → authorize → execute.

    Usage:
        class CreateAgentUseCase(UseCase[CreateAgentCommand, AgentDTO]):
            def __init__(self, repo: AgentRepository, event_bus: EventBus):
                self._repo = repo
                self._event_bus = event_bus

            async def _validate(self, input_data):
                if not input_data.name:
                    raise ValidationError("name", "Agent name is required")

            async def _execute(self, input_data):
                agent = Agent.create(name=input_data.name, ...)
                await self._repo.add(agent)
                await self._event_bus.publish_many(agent.collect_events())
                return AgentDTO.from_entity(agent)
    """

    async def __call__(self, input_data: TInput) -> TOutput:
        """Execute the use case with the full lifecycle."""
        await self._validate(input_data)
        await self._authorize(input_data)
        result = await self._execute(input_data)
        await self._post_execute(input_data, result)
        return result

    async def _validate(self, input_data: TInput) -> None:
        """Validate input data before execution.

        Override to add validation logic. Default is no-op.
        Raise ValidationError or BusinessRuleViolation on failure.
        """

    async def _authorize(self, input_data: TInput) -> None:
        """Check authorization before execution.

        Override to add authorization logic. Default is no-op.
        Raise AuthorizationError on failure.
        """

    @abstractmethod
    async def _execute(self, input_data: TInput) -> TOutput:
        """Execute the core business logic.

        This is the only method that MUST be implemented.
        """
        ...

    async def _post_execute(self, input_data: TInput, result: TOutput) -> None:
        """Post-execution hook for side effects (logging, events, etc.).

        Override to add post-execution logic. Default is no-op.
        """


class TransactionalUseCase(UseCase[TInput, TOutput], ABC):
    """Use case that wraps execution in a database transaction.

    Ensures atomicity: either all changes commit or all roll back.
    Domain events are dispatched only after successful commit.
    """

    async def __call__(self, input_data: TInput) -> TOutput:
        """Execute the use case within a transaction boundary."""
        await self._validate(input_data)
        await self._authorize(input_data)

        async with self._begin_transaction():
            result = await self._execute(input_data)

        await self._post_execute(input_data, result)
        return result

    @abstractmethod
    async def _begin_transaction(self) -> Any:
        """Begin a transaction context manager.

        Returns an async context manager that commits on success
        and rolls back on failure.
        """
        ...
