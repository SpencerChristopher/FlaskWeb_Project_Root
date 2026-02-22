"""
Authorization service utilities used by route handlers.
"""

from __future__ import annotations

from typing import Any

from flask import current_app, request

from src.exceptions import ForbiddenException, UnauthorizedException
from src.repositories.interfaces import UserRepository
from src.services.roles import (
    CAPABILITY_CONTENT_MANAGE,
    CAPABILITY_OPS_MANAGE,
    get_capabilities_for_role,
    get_capabilities_from_claims,
)


class AuthzService:
    """Domain-level authorization checks decoupled from route modules."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    def get_authenticated_user(self, user_id: str):
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("Authentication required or invalid credentials.")
        return user

    def require_capability(
        self,
        user_id: str,
        user_claims: dict[str, Any],
        capability: str,
        error_message: str,
    ):
        current_user = self.get_authenticated_user(user_id)
        user_capabilities = get_capabilities_for_role(current_user.role)

        if capability not in user_capabilities:
            raise ForbiddenException(error_message)

        claims_capabilities = get_capabilities_from_claims(user_claims)
        if capability not in claims_capabilities:
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user ID: {user_id} "
                f"with roles: {user_claims.get('roles', 'N/A')} "
                f"and capabilities: {user_claims.get('capabilities', 'N/A')} "
                f"from IP: {request.remote_addr}"
            )
            raise ForbiddenException(error_message)

        return current_user

    def require_admin(self, user_id: str, user_claims: dict[str, Any]):
        # Kept for backward compatibility with existing route decorators.
        return self.require_capability(
            user_id=user_id,
            user_claims=user_claims,
            capability=CAPABILITY_CONTENT_MANAGE,
            error_message="Admin access required.",
        )

    def require_content_admin(self, user_id: str, user_claims: dict[str, Any]):
        return self.require_capability(
            user_id=user_id,
            user_claims=user_claims,
            capability=CAPABILITY_CONTENT_MANAGE,
            error_message="Content admin access required.",
        )

    def require_ops_admin(self, user_id: str, user_claims: dict[str, Any]):
        return self.require_capability(
            user_id=user_id,
            user_claims=user_claims,
            capability=CAPABILITY_OPS_MANAGE,
            error_message="Ops admin access required.",
        )
