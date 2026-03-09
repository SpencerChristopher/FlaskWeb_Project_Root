"""
Authorization service utilities used by route handlers.
"""

from __future__ import annotations

from typing import Any

from flask import current_app, request

from src.exceptions import ForbiddenException, UnauthorizedException
from src.repositories.interfaces import UserRepository
from src.schemas import UserIdentity
from src.services.roles import (
    Permissions,
    get_permissions_for_role,
    get_permissions_from_claims,
)


class AuthzService:
    """Domain-level authorization checks decoupled from route modules.

    This service provides centralized logic for permission enforcement,
    role-based access control (RBAC), and identity verification using both
    database state and JWT claims.
    """

    def __init__(self, user_repository: UserRepository):
        """Initialize the AuthzService.

        Args:
            user_repository: Repository for identity lookups.
        """
        self._user_repository = user_repository

    def get_authenticated_user(self, user_id: str):
        """Retrieve and verify the existence of the user from the database.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            User: The persisted user instance.

        Raises:
            UnauthorizedException: If the user no longer exists in the system.
        """
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise UnauthorizedException(
                "Authentication required or invalid credentials."
            )
        return user

    def require_permission(
        self,
        user_id: str,
        user_claims: dict[str, Any],
        permission: str | list[str],
        error_message: str = "Access denied: insufficient permissions.",
    ) -> UserIdentity:
        """Enforce a granular permission check against both DB and JWT claims.

        This method ensures 'dual-validation':
        1. Validates that the token version matches the DB (Live Revocation).
        2. Validates that the authoritative DB role has the required permission.
        3. Validates that the JWT claims also possess the required permission.

        Args:
            user_id: The ID of the user attempting the action.
            user_claims: The decoded JWT payload.
            permission: A single permission string or a list of required permissions.
            error_message: Custom message for the ForbiddenException.

        Returns:
            UserIdentity: A lightweight DTO representing the verified user.

        Raises:
            UnauthorizedException: If the user is invalid or the token is expired/revoked.
            ForbiddenException: If the user lacks the required permissions.
        """
        # Fetch minimal identity fields from DB (Lazy Hydration)
        user_doc = self._user_repository.get_identity(user_id)
        if not user_doc:
            raise UnauthorizedException(
                "Authentication required or invalid credentials."
            )

        # 1. Token Version Check (Live Revocation)
        claim_version = user_claims.get("tv")
        if claim_version is None or user_doc.token_version != claim_version:
            current_app.logger.warning(
                f"Security event: Token version mismatch for user {user_id}. "
                f"DB: {user_doc.token_version}, JWT: {claim_version}. Access denied."
            )
            raise UnauthorizedException("Session has expired or been invalidated.")

        # Normalize required permissions to a set
        required_permissions = (
            {permission} if isinstance(permission, str) else set(permission)
        )

        # 2. DB Role Check (Authoritative)
        user_permissions = get_permissions_for_role(user_doc.role)
        if not (required_permissions & user_permissions):
            current_app.logger.warning(
                f"Permission mismatch: User {user_id} has role '{user_doc.role}' "
                f"which lacks any of the required permissions: {required_permissions}."
            )
            raise ForbiddenException(error_message)

        # 3. JWT Claim Check (State consistency)
        claims_permissions = get_permissions_from_claims(user_claims)
        if not (required_permissions & claims_permissions):
            current_app.logger.warning(
                f"Unauthorized access attempt: User {user_id} lacks required permissions "
                f"in JWT claims. Roles in claims: {user_claims.get('roles', 'N/A')}. "
                f"From IP: {request.remote_addr}"
            )
            raise ForbiddenException(error_message)

        # Return the lightweight DTO
        # Extract username from claims ('un') to save a DB fetch of the full User object
        return UserIdentity(
            id=str(user_doc.id),
            username=user_claims.get("un", "Unknown"),
            role=user_doc.role,
            token_version=user_doc.token_version,
        )

    def require_admin(self, user_id: str, user_claims: dict[str, Any]) -> UserIdentity:
        """Enforce administrator-level access.

        Args:
            user_id: The ID of the user.
            user_claims: The decoded JWT payload.

        Returns:
            UserIdentity: The verified identity.
        """
        return self.require_permission(
            user_id=user_id,
            user_claims=user_claims,
            permission=Permissions.CONTENT_MANAGE,
            error_message="Administrator access required.",
        )

    def require_content_admin(self, user_id: str, user_claims: dict[str, Any]):
        """Enforce content management access.

        Args:
            user_id: The ID of the user.
            user_claims: The decoded JWT payload.

        Returns:
            UserIdentity: The verified identity.
        """
        return self.require_permission(
            user_id=user_id,
            user_claims=user_claims,
            permission=Permissions.CONTENT_MANAGE,
            error_message="Content management access required.",
        )

    def get_user_capabilities(self, user_claims: dict[str, Any]) -> list[str]:
        """Extract the list of granular permissions available to the user.

        Used primarily for dynamic frontend UI discovery based on token claims.

        Args:
            user_claims: The decoded JWT payload.

        Returns:
            list[str]: Sorted list of permission strings.
        """
        return sorted(list(get_permissions_from_claims(user_claims)))
