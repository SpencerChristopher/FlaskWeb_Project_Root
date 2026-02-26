"""
MongoEngine-backed profile repository implementation.
Always treats the profile collection as a singleton.
"""

from __future__ import annotations
from typing import Optional
from pymongo.errors import PyMongoError

from src.exceptions import DatabaseConnectionException
from src.models.profile import Profile
from src.repositories.interfaces import ProfileRepository


class MongoProfileRepository(ProfileRepository):
    """MongoEngine implementation of profile singleton operations."""

    def get_profile(self) -> Optional[Profile]:
        try:
            return Profile.objects.first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching profile: {e}") from e

    def save(self, profile: Profile) -> Profile:
        try:
            return profile.save()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while saving profile: {e}") from e
