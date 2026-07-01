"""Specification pattern — composable query predicates for the domain layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """Specification pattern for composable domain query filters.

    Specifications express business rules as reusable, composable predicates.
    They can be evaluated in-memory or translated to SQL WHERE clauses
    by the infrastructure layer.

    Usage:
        class ActiveUsers(Specification[User]):
            def is_satisfied_by(self, entity: User) -> bool:
                return entity.is_active and not entity.is_deleted

        class InOrganization(Specification[User]):
            def __init__(self, org_id: UUID):
                self.org_id = org_id

            def is_satisfied_by(self, entity: User) -> bool:
                return entity.organization_id == self.org_id

        # Compose specifications
        spec = ActiveUsers() & InOrganization(org_id)
    """

    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if the entity satisfies this specification."""
        ...

    def to_query_params(self) -> dict[str, Any]:
        """Convert specification to query parameters for repository use.

        Override in subclasses to provide SQL-compatible filter params.
        Default returns empty dict (no filtering).
        """
        return {}

    def __and__(self, other: Specification[T]) -> AndSpecification[T]:
        return AndSpecification(self, other)

    def __or__(self, other: Specification[T]) -> OrSpecification[T]:
        return OrSpecification(self, other)

    def __invert__(self) -> NotSpecification[T]:
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Composite specification: both specs must be satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, entity: T) -> bool:
        return self._left.is_satisfied_by(entity) and self._right.is_satisfied_by(entity)

    def to_query_params(self) -> dict[str, Any]:
        params = self._left.to_query_params()
        params.update(self._right.to_query_params())
        return params


class OrSpecification(Specification[T]):
    """Composite specification: at least one spec must be satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, entity: T) -> bool:
        return self._left.is_satisfied_by(entity) or self._right.is_satisfied_by(entity)

    def to_query_params(self) -> dict[str, Any]:
        return {"_or": [self._left.to_query_params(), self._right.to_query_params()]}


class NotSpecification(Specification[T]):
    """Composite specification: the spec must NOT be satisfied."""

    def __init__(self, spec: Specification[T]) -> None:
        self._spec = spec

    def is_satisfied_by(self, entity: T) -> bool:
        return not self._spec.is_satisfied_by(entity)

    def to_query_params(self) -> dict[str, Any]:
        return {"_not": self._spec.to_query_params()}
