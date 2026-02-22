"""
Role and capability mapping helpers.
"""

from __future__ import annotations

from typing import Any

ROLE_USER = "user"
ROLE_EDITOR = "editor"
ROLE_ADMIN = "admin"
ROLE_CONTENT_ADMIN = "content_admin"
ROLE_OPS_ADMIN = "ops_admin"

CAPABILITY_CONTENT_MANAGE = "content.manage"
CAPABILITY_OPS_MANAGE = "ops.manage"

ROLE_CAPABILITIES = {
    ROLE_USER: frozenset(),
    ROLE_EDITOR: frozenset(),
    ROLE_CONTENT_ADMIN: frozenset({CAPABILITY_CONTENT_MANAGE}),
    ROLE_OPS_ADMIN: frozenset({CAPABILITY_OPS_MANAGE}),
    # Transitional legacy role: keeps both capability sets.
    ROLE_ADMIN: frozenset({CAPABILITY_CONTENT_MANAGE, CAPABILITY_OPS_MANAGE}),
}

SUPPORTED_ROLES = tuple(ROLE_CAPABILITIES.keys())


def get_capabilities_for_role(role: str) -> set[str]:
    return set(ROLE_CAPABILITIES.get(role, frozenset()))


def build_claim_roles_for_role(role: str) -> list[str]:
    if role == ROLE_ADMIN:
        return [ROLE_ADMIN, ROLE_CONTENT_ADMIN, ROLE_OPS_ADMIN]
    return [role]


def _normalize_claim_roles(raw_roles: Any) -> list[str]:
    if not isinstance(raw_roles, list):
        return []
    return [role for role in raw_roles if isinstance(role, str)]


def get_capabilities_from_claims(claims: dict[str, Any]) -> set[str]:
    capabilities: set[str] = set()

    raw_capabilities = claims.get("capabilities")
    if isinstance(raw_capabilities, list):
        capabilities.update(cap for cap in raw_capabilities if isinstance(cap, str))

    for role in _normalize_claim_roles(claims.get("roles")):
        capabilities.update(get_capabilities_for_role(role))

    return capabilities
