"""Password value object for secure hashing and verification."""

from __future__ import annotations

from passlib.context import CryptContext

from converse_shared.domain.value_objects import ValueObject

# Setup bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHash(ValueObject):
    """Value object representing a hashed password."""

    value: str

    @classmethod
    def create(cls, raw_password: str) -> PasswordHash:
        """Hash a raw password and create the value object."""
        if len(raw_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        hashed = pwd_context.hash(raw_password)
        return cls(value=hashed)

    def verify(self, raw_password: str) -> bool:
        """Verify a raw password against this hash."""
        return pwd_context.verify(raw_password, self.value)

    def __str__(self) -> str:
        return self.value
