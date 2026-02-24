"""
Authorization service utilities used by route handlers.
"""

from __future__ import annotations

from typing import Any

from flask import current_app, request

from src.exceptions import ForbiddenException, UnauthorizedException
from src.repositories.interfaces import UserRepository
from src.services.roles import (
    Permissions,
    get_permissions_for_role,
    get_permissions_from_claims,
)


class AuthzService:
    """Domain-level authorization checks decoupled from route modules."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    def get_authenticated_user(self, user_id: str):
        """Retrieve and verify the existence of the user from the database."""
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("Authentication required or invalid credentials.")
        return user

    def require_permission(
        self,
        user_id: str,
        user_claims: dict[str, Any],
        permission: str,
        error_message: str = "Access denied: insufficient permissions.",
    ):
        """
        Enforce a granular permission check.
        Verifies both the database-stored role and the JWT claims.
        """
        current_user = self.get_authenticated_user(user_id)
        
        # 1. DB Role Check (Authoritative)
        user_permissions = get_permissions_for_role(current_user.role)
        if permission not in user_permissions:
            current_app.logger.warning(
                f"Permission mismatch: User {user_id} has role '{current_user.role}' "
                f"which lacks required permission '{permission}'."
            )
            raise ForbiddenException(error_message)

        # 2. JWT Claim Check (Revocation/State consistency)
        claims_permissions = get_permissions_from_claims(user_claims)
        if permission not in claims_permissions:
            current_app.logger.warning(
                f"Unauthorized access attempt: User {user_id} lacks permission '{permission}' "
                f"in JWT claims. Roles in claims: {user_claims.get('roles', 'N/A')}. "
                f"From IP: {request.remote_addr}"
            )
            raise ForbiddenException(error_message)

        return current_user

    def require_admin(self, user_id: str, user_claims: dict[str, Any]):
        """Legacy helper for admin-level routes."""
        return self.require_permission(
            user_id=user_id,
            user_claims=user_claims,
            permission=Permissions.CONTENT_MANAGE,
            error_message="Administrator access required.",
        )

    def require_content_admin(self, user_id: str, user_claims: dict[str, Any]):
        """Transitional helper mapping to content management."""
        return self.require_permission(
            user_id=user_id,
            user_claims=user_claims,
            permission=Permissions.CONTENT_MANAGE,
            error_message="Content management access required.",
        )
