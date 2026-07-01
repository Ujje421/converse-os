"""Unit tests for Audit Service Domain Entities."""

import uuid
from datetime import datetime, UTC

from audit_service.domain.entities.audit_log import AuditLog


def test_create_audit_log():
    """Test audit log creation."""
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    log = AuditLog.create(
        tenant_id=tenant_id,
        user_id=user_id,
        action="CREATE",
        resource_type="AGENT",
        resource_id="agent-123",
        details={"name": "Support Bot"},
        ip_address="127.0.0.1",
    )
    
    assert log.tenant_id == tenant_id
    assert log.user_id == user_id
    assert log.action == "CREATE"
    assert log.resource_type == "AGENT"
    assert log.resource_id == "agent-123"
    assert log.details == {"name": "Support Bot"}
    assert log.ip_address == "127.0.0.1"
    assert isinstance(log.created_at, datetime)
