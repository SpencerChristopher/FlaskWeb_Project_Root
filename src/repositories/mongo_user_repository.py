"""
MongoEngine-backed user repository implementation.
"""

from __future__ import annotations

from typing import Optional

from src.models.user import User
from src.repositories.interfaces import UserRepository


from pymongo.errors import PyMongoError
from src.exceptions import DatabaseConnectionException


class MongoUserRepository(UserRepository):
    """MongoEngine implementation of user persistence operations."""

    def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            return User.objects(id=user_id).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching user by ID: {e}") from e

    def get_identity(self, user_id: str) -> Optional[User]:
        try:
            # Use projection to fetch only minimal fields required for UserIdentity DTO
            return User.objects(id=user_id).only('id', 'role', 'token_version').first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching user identity: {e}") from e

    def get_by_username(self, username: str) -> Optional[User]:
        try:
            return User.objects(username=username).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching user by username: {e}") from e

    def save(self, user: User) -> User:
        try:
            return user.save()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while saving user: {e}") from e

    def delete(self, user: User) -> None:
        try:
            user.delete()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while deleting user: {e}") from e
