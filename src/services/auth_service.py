"""
Auth service for user credential and profile operations.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from src.events import dispatch_event, user_deleted, user_role_changed
from src.exceptions import UnauthorizedException
from src.models.user import User
from src.repositories.interfaces import UserRepository
from src.services.roles import build_claim_roles_for_role

if TYPE_CHECKING:
    from src.services.session_service import SessionService


class AuthService:
    """Application service for auth-related user workflows."""

    def __init__(self, user_repository: UserRepository, session_service: SessionService | None = None):
        self._user_repository = user_repository
        self._session_service = session_service

    def authenticate(self, username: str, password: str) -> User:
        user = self._user_repository.get_by_username(username)
        if not user or not user.check_password(password):
            raise UnauthorizedException("Invalid username or password")
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self._user_repository.get_by_id(user_id)

    def get_user_or_raise(self, user_id: str, message: str = "Invalid user") -> User:
        user = self.get_user(user_id)
        if not user:
            raise UnauthorizedException(message)
        return user

    def build_token_claims(self, user: User) -> dict[str, Any]:
        """
        Build the claims to be included in the JWT.
        Includes minimal role, username, and version info to enable stateless 
        authorization with backend-derived permissions and display metadata.
        """
        return {
            "roles": build_claim_roles_for_role(user.role),
            "un": user.username,
            "tv": user.token_version,
        }

    def change_password(
        self, *, user_id: str, current_password: str, new_password: str
    ) -> None:
        user = self.get_user_or_raise(user_id)
        if not user.check_password(current_password):
            raise UnauthorizedException("Invalid current password")

        user.set_password(new_password)
        self._user_repository.save(user)

    def change_role(self, *, user_id: str, role: str) -> User:
        user = self.get_user_or_raise(user_id)
        if user.role != role:
            user.role = role
            user.token_version = (user.token_version or 0) + 1
            self._user_repository.save(user)
            dispatch_event(user_role_changed, self, user_id=str(user.id), new_role=role)
        return user

    def delete_user(self, *, user_id: str) -> None:
        user = self.get_user_or_raise(user_id)
        persisted_user_id = str(user.id)
        self._user_repository.delete(user)
        dispatch_event(user_deleted, user, user_id=persisted_user_id)
