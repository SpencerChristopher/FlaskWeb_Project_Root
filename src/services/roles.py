"""
Role and permission mapping definitions for the modular monolith.
"""

from __future__ import annotations
from typing import Any

# Role Constants
ROLE_ADMIN = "admin"
ROLE_AUTHOR = "author"
ROLE_MEMBER = "member"


# Permission Constants
class Permissions:
    CONTENT_MANAGE = "content:manage"  # Full CRUD on all content
    CONTENT_AUTHOR = "content:author"  # Full CRUD on personal content
    PROFILE_MANAGE = "profile:manage"  # Manage developer profile/socials
    USERS_MANAGE = "users:manage"  # User management and roles
    SYSTEM_VIEW_LOGS = "system:view_logs"  # Diagnostic access


ROLE_PERMISSIONS = {
    ROLE_ADMIN: frozenset(
        {
            Permissions.CONTENT_MANAGE,
            Permissions.PROFILE_MANAGE,
            Permissions.USERS_MANAGE,
            Permissions.SYSTEM_VIEW_LOGS,
        }
    ),
    ROLE_AUTHOR: frozenset({Permissions.CONTENT_AUTHOR}),
    ROLE_MEMBER: frozenset(),  # Read-only access by default
}

SUPPORTED_ROLES = tuple(ROLE_PERMISSIONS.keys())


def get_permissions_for_role(role: str) -> set[str]:
    """Retrieve the set of permissions assigned to a specific role."""
    return set(ROLE_PERMISSIONS.get(role, frozenset()))


def build_claim_roles_for_role(role: str) -> list[str]:
    """
    Build the list of roles to be included in the JWT 'roles' claim.
    Provides backward compatibility for role-based systems.
    """
    return [role]


def _normalize_claim_roles(raw_roles: Any) -> list[str]:
    """Helper to ensure role claims are handled as a list of strings."""
    if not isinstance(raw_roles, list):
        return []
    return [role for role in raw_roles if isinstance(role, str)]


def get_permissions_from_claims(claims: dict[str, Any]) -> set[str]:
    """
    Extract and derive permissions from JWT claims.
    Derives permissions from the 'roles' claim using ROLE_PERMISSIONS mapping.
    """
    permissions: set[str] = set()

    # Derive permissions from roles found in claims
    for role in _normalize_claim_roles(claims.get("roles")):
        permissions.update(get_permissions_for_role(role))

    return permissions
