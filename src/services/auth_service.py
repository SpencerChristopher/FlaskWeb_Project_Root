"""
Auth service for user credential and profile operations.
"""

from __future__ import annotations

from typing import Any, Optional

from src.exceptions import UnauthorizedException
from src.models.user import User
from src.repositories.interfaces import UserRepository


class AuthService:
    """Application service for auth-related user workflows."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

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
        return {"roles": [user.role], "tv": user.token_version}

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
        return user
