"""Mediator pattern — in-process command/query dispatcher for CQRS."""

from __future__ import annotations

from typing import Any

import structlog

from converse_shared.application.command import Command, CommandHandler, CommandResult
from converse_shared.application.query import Query, QueryHandler, QueryResult

logger = structlog.get_logger()


class Mediator:
    """In-process mediator for CQRS command/query dispatch.

    The mediator decouples command/query issuers from their handlers,
    enabling clean separation of concerns and making it easy to add
    cross-cutting behaviors (logging, validation, authorization) via
    pipeline behaviors.

    Usage:
        mediator = Mediator()
        mediator.register_command_handler(CreateUser, CreateUserHandler(repo))
        mediator.register_query_handler(GetUser, GetUserHandler(repo))

        result = await mediator.send(CreateUser(name="Alice"))
        user = await mediator.query(GetUser(user_id=...))
    """

    def __init__(self) -> None:
        self._command_handlers: dict[type[Command], CommandHandler[Any]] = {}
        self._query_handlers: dict[type[Query], QueryHandler[Any]] = {}
        self._pipeline_behaviors: list[PipelineBehavior] = []

    def register_command_handler(
        self,
        command_type: type[Command],
        handler: CommandHandler[Any],
    ) -> None:
        """Register a handler for a specific command type."""
        if command_type in self._command_handlers:
            logger.warning(
                "overwriting_command_handler",
                command_type=command_type.__name__,
            )
        self._command_handlers[command_type] = handler
        logger.debug("registered_command_handler", command_type=command_type.__name__)

    def register_query_handler(
        self,
        query_type: type[Query],
        handler: QueryHandler[Any],
    ) -> None:
        """Register a handler for a specific query type."""
        if query_type in self._query_handlers:
            logger.warning(
                "overwriting_query_handler",
                query_type=query_type.__name__,
            )
        self._query_handlers[query_type] = handler
        logger.debug("registered_query_handler", query_type=query_type.__name__)

    def add_pipeline_behavior(self, behavior: PipelineBehavior) -> None:
        """Add a pipeline behavior that wraps all command/query handling."""
        self._pipeline_behaviors.append(behavior)

    async def send(self, command: Command) -> CommandResult[Any]:
        """Dispatch a command to its registered handler.

        Args:
            command: The command to dispatch.

        Returns:
            CommandResult from the handler.

        Raises:
            ValueError: If no handler is registered for the command type.
        """
        handler = self._command_handlers.get(type(command))
        if handler is None:
            raise ValueError(
                f"No command handler registered for {type(command).__name__}"
            )

        logger.info(
            "dispatching_command",
            command_type=type(command).__name__,
            command_id=str(command.command_id),
            tenant_id=str(command.tenant_id) if command.tenant_id else None,
        )

        # Execute through pipeline behaviors
        async def execute() -> CommandResult[Any]:
            return await handler.handle(command)

        result = await self._execute_pipeline(command, execute)
        return result

    async def query(self, query: Query) -> QueryResult[Any]:
        """Dispatch a query to its registered handler.

        Args:
            query: The query to dispatch.

        Returns:
            QueryResult from the handler.

        Raises:
            ValueError: If no handler is registered for the query type.
        """
        handler = self._query_handlers.get(type(query))
        if handler is None:
            raise ValueError(
                f"No query handler registered for {type(query).__name__}"
            )

        logger.info(
            "dispatching_query",
            query_type=type(query).__name__,
            query_id=str(query.query_id),
            tenant_id=str(query.tenant_id) if query.tenant_id else None,
        )

        async def execute() -> QueryResult[Any]:
            return await handler.handle(query)

        result = await self._execute_pipeline(query, execute)
        return result

    async def _execute_pipeline(
        self,
        request: Command | Query,
        final_handler: Any,
    ) -> Any:
        """Execute the pipeline behaviors around the final handler."""
        if not self._pipeline_behaviors:
            return await final_handler()

        # Build pipeline chain (behaviors wrap the handler)
        current = final_handler
        for behavior in reversed(self._pipeline_behaviors):
            prev = current

            async def make_next(b: PipelineBehavior, p: Any) -> Any:
                return await b.handle(request, p)

            current = lambda b=behavior, p=prev: make_next(b, p)  # noqa: E731

        return await current()


class PipelineBehavior:
    """Pipeline behavior for cross-cutting concerns.

    Behaviors wrap the command/query execution, allowing you to add
    logging, validation, authorization, caching, etc.

    Usage:
        class LoggingBehavior(PipelineBehavior):
            async def handle(self, request, next_handler):
                logger.info("handling", request_type=type(request).__name__)
                result = await next_handler()
                logger.info("handled", request_type=type(request).__name__)
                return result
    """

    async def handle(self, request: Command | Query, next_handler: Any) -> Any:
        """Execute the behavior and call the next handler in the pipeline."""
        return await next_handler()
