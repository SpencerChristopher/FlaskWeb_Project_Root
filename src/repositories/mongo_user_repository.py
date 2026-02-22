"""
MongoEngine-backed user repository implementation.
"""

from __future__ import annotations

from typing import Optional

from src.models.user import User
from src.repositories.interfaces import UserRepository


class MongoUserRepository(UserRepository):
    """MongoEngine implementation of user persistence operations."""

    def get_by_id(self, user_id: str) -> Optional[User]:
        return User.objects(id=user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return User.objects(username=username).first()

    def save(self, user: User) -> User:
        return user.save()

    def delete(self, user: User) -> None:
        user.delete()
