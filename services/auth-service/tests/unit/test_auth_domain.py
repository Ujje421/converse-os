"""Unit tests for Auth Service Domain Entities."""

import uuid
from datetime import datetime, UTC

import pytest
from converse_shared.domain.value_objects import Email

from auth_service.domain.entities.user_credentials import UserCredentials
from auth_service.domain.value_objects.password import PasswordHash


def test_create_user_credentials():
    """Test user credentials creation."""
    user_id = uuid.uuid4()
    email = Email("test@example.com")
    pwd_hash = PasswordHash.create("secure_password123")
    
    credentials = UserCredentials.create(
        user_id=user_id,
        email=email,
        password_hash=pwd_hash,
    )
    
    assert credentials.user_id == user_id
    assert credentials.email == email
    assert credentials.is_active is True
    assert credentials.failed_login_attempts == 0
    assert not credentials.is_locked()


def test_password_hashing():
    """Test password value object hashing and verification."""
    raw_password = "secure_password123"
    pwd_hash = PasswordHash.create(raw_password)
    
    assert pwd_hash.verify(raw_password) is True
    assert pwd_hash.verify("wrong_password") is False


def test_account_locking():
    """Test failed logins and account lock logic."""
    credentials = UserCredentials.create(
        user_id=uuid.uuid4(),
        email=Email("test@example.com"),
        password_hash=PasswordHash.create("secure_password123"),
    )
    
    # Simulate 5 failed logins
    for _ in range(5):
        credentials.record_failed_login(max_attempts=5, lock_duration_minutes=15)
        
    assert credentials.failed_login_attempts == 5
    assert credentials.is_locked() is True
    
    # Successful login resets the attempts
    credentials.record_successful_login()
    assert credentials.failed_login_attempts == 0
    assert credentials.is_locked() is False
    
