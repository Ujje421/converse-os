"""Unit tests for Org Service Domain Entities."""

import uuid
import pytest

from org_service.domain.entities.organization import Organization


def test_create_organization():
    """Test organization creation and owner assignment."""
    owner_id = uuid.uuid4()
    
    org = Organization.create(
        name="Acme Corp",
        slug="acme-corp",
        owner_id=owner_id,
    )
    
    assert org.name == "Acme Corp"
    assert org.slug == "acme-corp"
    assert org.billing_plan == "FREE"
    assert org.is_active is True
    
    # Check owner
    assert len(org.members) == 1
    assert org.members[0].user_id == owner_id
    assert org.members[0].role == "OWNER"


def test_add_remove_member():
    """Test adding and removing members."""
    owner_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    org = Organization.create(
        name="Acme Corp",
        slug="acme-corp",
        owner_id=owner_id,
    )
    
    org.add_member(user_id=user_id, role="MEMBER")
    assert len(org.members) == 2
    
    # Can't add twice
    with pytest.raises(ValueError):
        org.add_member(user_id=user_id, role="ADMIN")
        
    org.remove_member(user_id=user_id)
    assert len(org.members) == 1
    
    # Can't remove the only owner
    with pytest.raises(ValueError):
        org.remove_member(user_id=owner_id)
