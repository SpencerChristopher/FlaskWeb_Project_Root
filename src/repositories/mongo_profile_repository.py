"""
MongoEngine-backed profile repository implementation.
Always treats the profile collection as a singleton.
"""

from __future__ import annotations
from typing import Optional
from pymongo.errors import PyMongoError

from src.exceptions import DatabaseConnectionException
from src.models.profile import Profile, PROFILE_SINGLETON_KEY
from src.repositories.interfaces import ProfileRepository


class MongoProfileRepository(ProfileRepository):
    """MongoEngine implementation of profile singleton operations."""

    def get_profile(self) -> Optional[Profile]:
        try:
            profile = Profile.objects(singleton_key=PROFILE_SINGLETON_KEY).first()
            if profile:
                return profile
            profile = Profile.objects.first()
            if profile and not getattr(profile, "singleton_key", None):
                profile.singleton_key = PROFILE_SINGLETON_KEY
                profile.save()
            return profile
        except PyMongoError as e:
            raise DatabaseConnectionException(
                f"Database error while fetching profile: {e}"
            ) from e

    def save(self, profile: Profile) -> Profile:
        try:
            profile.singleton_key = PROFILE_SINGLETON_KEY
            return profile.save()
        except PyMongoError as e:
            raise DatabaseConnectionException(
                f"Database error while saving profile: {e}"
            ) from e
