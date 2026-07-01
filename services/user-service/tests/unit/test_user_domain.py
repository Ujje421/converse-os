"""Unit tests for User Service Domain Entities."""

import uuid

from converse_shared.domain.value_objects import Email
from user_service.domain.entities.user_profile import UserProfile


def test_create_user_profile():
    """Test user profile creation."""
    user_id = uuid.uuid4()
    email = Email("user@example.com")
    
    profile = UserProfile.create(
        user_id=user_id,
        email=email,
        first_name="Jane",
        last_name="Doe"
    )
    
    assert profile.id == user_id
    assert profile.email == email
    assert profile.first_name == "Jane"
    assert profile.last_name == "Doe"
    assert profile.timezone == "UTC"
    assert profile.preferences == {}


def test_update_user_profile():
    """Test user profile updates."""
    profile = UserProfile.create(
        user_id=uuid.uuid4(),
        email=Email("user@example.com"),
    )
    
    profile.update_profile(
        first_name="John",
        last_name="Smith",
        timezone="America/New_York"
    )
    
    assert profile.first_name == "John"
    assert profile.last_name == "Smith"
    assert profile.timezone == "America/New_York"


def test_update_preferences():
    """Test user preferences updates."""
    profile = UserProfile.create(
        user_id=uuid.uuid4(),
        email=Email("user@example.com"),
    )
    
    profile.update_preferences({"theme": "dark", "notifications_enabled": True})
    
    assert profile.preferences["theme"] == "dark"
    assert profile.preferences["notifications_enabled"] is True
