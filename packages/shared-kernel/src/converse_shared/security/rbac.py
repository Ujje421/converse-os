"""RBAC — Role-Based Access Control with permission policies and decorators."""

from __future__ import annotations

import functools
import uuid
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel

from converse_shared.domain.exceptions import AuthorizationError

logger = structlog.get_logger()


class Permission(str, Enum):
    """Platform permissions — fine-grained actions on resources."""

    # Organization
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    ORG_MANAGE_MEMBERS = "org:manage_members"
    ORG_MANAGE_SETTINGS = "org:manage_settings"

    # Projects
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # Agents
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_DEPLOY = "agent:deploy"
    AGENT_TEST = "agent:test"

    # Conversations
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_MANAGE = "conversation:manage"
    CONVERSATION_EXPORT = "conversation:export"

    # Knowledge Base
    KB_CREATE = "kb:create"
    KB_READ = "kb:read"
    KB_UPDATE = "kb:update"
    KB_DELETE = "kb:delete"

    # Prompts
    PROMPT_CREATE = "prompt:create"
    PROMPT_READ = "prompt:read"
    PROMPT_UPDATE = "prompt:update"
    PROMPT_DELETE = "prompt:delete"
    PROMPT_PUBLISH = "prompt:publish"

    # Workflows
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"

    # Webhooks
    WEBHOOK_CREATE = "webhook:create"
    WEBHOOK_READ = "webhook:read"
    WEBHOOK_UPDATE = "webhook:update"
    WEBHOOK_DELETE = "webhook:delete"

    # Analytics
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"

    # Users
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Billing
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"

    # Audit
    AUDIT_READ = "audit:read"

    # API Keys
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_DELETE = "api_key:delete"

    # Channels
    CHANNEL_CREATE = "channel:create"
    CHANNEL_READ = "channel:read"
    CHANNEL_UPDATE = "channel:update"
    CHANNEL_DELETE = "channel:delete"

    # Admin (platform-level)
    ADMIN_FULL_ACCESS = "admin:full_access"
    ADMIN_MANAGE_TENANTS = "admin:manage_tenants"
    ADMIN_VIEW_METRICS = "admin:view_metrics"


class Role(str, Enum):
    """Platform roles with predefined permission sets."""

    PLATFORM_ADMIN = "platform_admin"
    ORG_OWNER = "org_owner"
    ORG_ADMIN = "org_admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"


# Role → Permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.PLATFORM_ADMIN: set(Permission),  # All permissions
    Role.ORG_OWNER: {
        Permission.ORG_READ, Permission.ORG_UPDATE, Permission.ORG_DELETE,
        Permission.ORG_MANAGE_MEMBERS, Permission.ORG_MANAGE_SETTINGS,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.AGENT_CREATE, Permission.AGENT_READ, Permission.AGENT_UPDATE, Permission.AGENT_DELETE,
        Permission.AGENT_DEPLOY, Permission.AGENT_TEST,
        Permission.CONVERSATION_READ, Permission.CONVERSATION_MANAGE, Permission.CONVERSATION_EXPORT,
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.PROMPT_CREATE, Permission.PROMPT_READ, Permission.PROMPT_UPDATE, Permission.PROMPT_DELETE,
        Permission.PROMPT_PUBLISH,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_UPDATE, Permission.WORKFLOW_DELETE,
        Permission.WORKFLOW_EXECUTE,
        Permission.WEBHOOK_CREATE, Permission.WEBHOOK_READ, Permission.WEBHOOK_UPDATE, Permission.WEBHOOK_DELETE,
        Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
        Permission.USER_READ, Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.USER_MANAGE_ROLES,
        Permission.BILLING_READ, Permission.BILLING_MANAGE,
        Permission.AUDIT_READ,
        Permission.API_KEY_CREATE, Permission.API_KEY_READ, Permission.API_KEY_DELETE,
        Permission.CHANNEL_CREATE, Permission.CHANNEL_READ, Permission.CHANNEL_UPDATE, Permission.CHANNEL_DELETE,
    },
    Role.ORG_ADMIN: {
        Permission.ORG_READ, Permission.ORG_UPDATE, Permission.ORG_MANAGE_MEMBERS, Permission.ORG_MANAGE_SETTINGS,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.AGENT_CREATE, Permission.AGENT_READ, Permission.AGENT_UPDATE, Permission.AGENT_DELETE,
        Permission.AGENT_DEPLOY, Permission.AGENT_TEST,
        Permission.CONVERSATION_READ, Permission.CONVERSATION_MANAGE, Permission.CONVERSATION_EXPORT,
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.PROMPT_CREATE, Permission.PROMPT_READ, Permission.PROMPT_UPDATE, Permission.PROMPT_DELETE,
        Permission.PROMPT_PUBLISH,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_UPDATE, Permission.WORKFLOW_DELETE,
        Permission.WORKFLOW_EXECUTE,
        Permission.WEBHOOK_CREATE, Permission.WEBHOOK_READ, Permission.WEBHOOK_UPDATE, Permission.WEBHOOK_DELETE,
        Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
        Permission.USER_READ, Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_MANAGE_ROLES,
        Permission.BILLING_READ,
        Permission.AUDIT_READ,
        Permission.API_KEY_CREATE, Permission.API_KEY_READ, Permission.API_KEY_DELETE,
        Permission.CHANNEL_CREATE, Permission.CHANNEL_READ, Permission.CHANNEL_UPDATE, Permission.CHANNEL_DELETE,
    },
    Role.PROJECT_MANAGER: {
        Permission.ORG_READ,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.AGENT_CREATE, Permission.AGENT_READ, Permission.AGENT_UPDATE,
        Permission.AGENT_DEPLOY, Permission.AGENT_TEST,
        Permission.CONVERSATION_READ, Permission.CONVERSATION_MANAGE,
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE,
        Permission.PROMPT_CREATE, Permission.PROMPT_READ, Permission.PROMPT_UPDATE, Permission.PROMPT_PUBLISH,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_UPDATE, Permission.WORKFLOW_EXECUTE,
        Permission.WEBHOOK_CREATE, Permission.WEBHOOK_READ, Permission.WEBHOOK_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.USER_READ,
        Permission.API_KEY_CREATE, Permission.API_KEY_READ,
        Permission.CHANNEL_READ, Permission.CHANNEL_UPDATE,
    },
    Role.DEVELOPER: {
        Permission.ORG_READ,
        Permission.PROJECT_READ,
        Permission.AGENT_CREATE, Permission.AGENT_READ, Permission.AGENT_UPDATE, Permission.AGENT_TEST,
        Permission.CONVERSATION_READ,
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE,
        Permission.PROMPT_CREATE, Permission.PROMPT_READ, Permission.PROMPT_UPDATE,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_UPDATE, Permission.WORKFLOW_EXECUTE,
        Permission.WEBHOOK_CREATE, Permission.WEBHOOK_READ, Permission.WEBHOOK_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.API_KEY_CREATE, Permission.API_KEY_READ,
        Permission.CHANNEL_READ,
    },
    Role.ANALYST: {
        Permission.ORG_READ,
        Permission.PROJECT_READ,
        Permission.AGENT_READ,
        Permission.CONVERSATION_READ, Permission.CONVERSATION_EXPORT,
        Permission.KB_READ,
        Permission.PROMPT_READ,
        Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
    },
    Role.VIEWER: {
        Permission.ORG_READ,
        Permission.PROJECT_READ,
        Permission.AGENT_READ,
        Permission.CONVERSATION_READ,
        Permission.KB_READ,
        Permission.PROMPT_READ,
        Permission.ANALYTICS_READ,
    },
}


class PolicyEngine:
    """RBAC policy evaluation engine.

    Evaluates whether a user with given roles has the required permissions
    for a specific action on a resource.

    Usage:
        engine = PolicyEngine()
        engine.check_permission(roles=["org_admin"], required=Permission.AGENT_CREATE)
    """

    def get_permissions_for_roles(self, roles: list[str]) -> set[Permission]:
        """Resolve all permissions for a set of roles."""
        permissions: set[Permission] = set()
        for role_name in roles:
            try:
                role = Role(role_name)
                permissions.update(ROLE_PERMISSIONS.get(role, set()))
            except ValueError:
                logger.warning("unknown_role", role=role_name)
        return permissions

    def has_permission(self, roles: list[str], required: Permission) -> bool:
        """Check if the given roles grant the required permission."""
        permissions = self.get_permissions_for_roles(roles)
        return required in permissions

    def check_permission(
        self,
        roles: list[str],
        required: Permission,
        resource: str = "",
    ) -> None:
        """Check permission and raise AuthorizationError if denied."""
        if not self.has_permission(roles, required):
            raise AuthorizationError(
                action=required.value,
                resource=resource,
                details={"roles": roles, "required_permission": required.value},
            )

    def has_any_permission(self, roles: list[str], required: list[Permission]) -> bool:
        """Check if the given roles grant any of the required permissions."""
        permissions = self.get_permissions_for_roles(roles)
        return bool(permissions.intersection(required))

    def has_all_permissions(self, roles: list[str], required: list[Permission]) -> bool:
        """Check if the given roles grant all of the required permissions."""
        permissions = self.get_permissions_for_roles(roles)
        return all(p in permissions for p in required)


# Global policy engine instance
policy_engine = PolicyEngine()


def require_permission(permission: Permission, resource: str = ""):
    """Decorator for protecting endpoints with permission checks.

    The decorated function must have a 'current_user' parameter with a
    'roles' attribute.

    Usage:
        @require_permission(Permission.AGENT_CREATE, resource="agent")
        async def create_agent(request, current_user):
            ...
    """

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise AuthorizationError(
                    action=permission.value,
                    resource=resource,
                    details={"reason": "No authenticated user"},
                )

            roles = getattr(current_user, "roles", [])
            policy_engine.check_permission(roles=roles, required=permission, resource=resource)
            return await func(*args, **kwargs)

        return wrapper
    return decorator
