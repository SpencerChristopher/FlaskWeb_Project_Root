"""
Authorization service utilities used by route handlers.
"""

from __future__ import annotations

from typing import Any

from flask import current_app, request

from src.exceptions import ForbiddenException, UnauthorizedException
from src.repositories.interfaces import UserRepository


class AuthzService:
    """Domain-level authorization checks decoupled from route modules."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    def get_authenticated_user(self, user_id: str):
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("Authentication required or invalid credentials.")
        return user

    def require_admin(self, user_id: str, user_claims: dict[str, Any]):
        current_user = self.get_authenticated_user(user_id)

        if current_user.role != "admin":
            raise ForbiddenException("Admin access required.")

        if "roles" not in user_claims or "admin" not in user_claims["roles"]:
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user ID: {user_id} "
                f"with roles: {user_claims.get('roles', 'N/A')} from IP: {request.remote_addr}"
            )
            raise ForbiddenException("Admin access required.")

        return current_user
