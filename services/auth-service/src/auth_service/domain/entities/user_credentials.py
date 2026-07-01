"""Domain entity for User Credentials."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from converse_shared.domain.aggregate_root import AggregateRoot
from converse_shared.domain.value_objects import Email

from auth_service.domain.value_objects.password import PasswordHash


class UserCredentials(AggregateRoot):
    """Aggregate root for managing user authentication credentials."""

    user_id: uuid.UUID
    email: Email
    password_hash: PasswordHash | None = None
    is_active: bool = True
    is_email_verified: bool = False
    last_login_at: datetime | None = None
    failed_login_attempts: int = 0
    locked_until: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: uuid.UUID,
        email: Email,
        password_hash: PasswordHash | None = None,
        is_active: bool = True,
    ) -> UserCredentials:
        """Create new user credentials."""
        return cls(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
            is_active=is_active,
        )

    def record_successful_login(self) -> None:
        """Record a successful login and reset failed attempts."""
        self.last_login_at = datetime.now(UTC)
        self.failed_login_attempts = 0
        self.locked_until = None
        self.mark_updated()

    def record_failed_login(self, max_attempts: int = 5, lock_duration_minutes: int = 15) -> None:
        """Record a failed login attempt and potentially lock the account."""
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.now(UTC) + timedelta(minutes=lock_duration_minutes)
            
        self.mark_updated()

    def is_locked(self) -> bool:
        """Check if the account is currently locked due to failed attempts."""
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now(UTC)

    def update_password(self, new_password_hash: PasswordHash) -> None:
        """Update the user's password."""
        self.password_hash = new_password_hash
        self.mark_updated()
        # self._register_event(PasswordChangedEvent(user_id=self.user_id))
