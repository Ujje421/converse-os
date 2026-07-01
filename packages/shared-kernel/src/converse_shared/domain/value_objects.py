"""Value Objects — immutable domain primitives with validation."""

from __future__ import annotations

import re
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ValueObject(BaseModel):
    """Base class for value objects.

    Value objects are immutable, compared by their attributes rather than identity.
    They encapsulate validation rules for domain primitives.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.model_dump().items())))


class TenantId(ValueObject):
    """Tenant identifier value object."""

    value: uuid.UUID

    @classmethod
    def generate(cls) -> TenantId:
        return cls(value=uuid.uuid4())

    def __str__(self) -> str:
        return str(self.value)


class UserId(ValueObject):
    """User identifier value object."""

    value: uuid.UUID

    @classmethod
    def generate(cls) -> UserId:
        return cls(value=uuid.uuid4())

    def __str__(self) -> str:
        return str(self.value)


class Email(ValueObject):
    """Email address value object with validation."""

    value: str

    @field_validator("value")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email address: {v}")
        return v.lower().strip()

    def __str__(self) -> str:
        return self.value


class Money(ValueObject):
    """Monetary value object with currency."""

    amount: int = Field(description="Amount in smallest currency unit (cents)")
    currency: str = Field(default="USD", max_length=3, min_length=3)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

    @property
    def decimal_amount(self) -> float:
        return self.amount / 100

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def multiply(self, factor: int) -> Money:
        return Money(amount=self.amount * factor, currency=self.currency)


class Pagination(BaseModel):
    """Pagination parameters for list queries."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class SortOrder(BaseModel):
    """Sort order specification."""

    model_config = ConfigDict(frozen=True)

    field: str
    direction: str = Field(default="asc", pattern="^(asc|desc)$")


class TimeRange(BaseModel):
    """Time range filter."""

    model_config = ConfigDict(frozen=True)

    from datetime import datetime as _datetime

    start: _datetime | None = None
    end: _datetime | None = None

    @field_validator("end")
    @classmethod
    def validate_range(cls, v: _datetime | None, info: Any) -> _datetime | None:
        start = info.data.get("start")
        if v is not None and start is not None and v < start:
            raise ValueError("End time must be after start time")
        return v


class SlugVO(ValueObject):
    """URL-safe slug value object."""

    value: str = Field(max_length=128)

    @field_validator("value")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid slug: {v}. Must be lowercase alphanumeric with hyphens.")
        return v

    def __str__(self) -> str:
        return self.value
