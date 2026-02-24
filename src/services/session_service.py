"""
Session service for managing stateful JWT session data in Redis.
"""

from __future__ import annotations
from typing import Optional
from redis import Redis


class SessionService:
    """
    Handles stateful session tracking to enable features like multi-device invalidation
    and performant token revocation.
    """

    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        self._prefix = "session:"

    def set_active_refresh_token(self, user_id: str, jti: str, ttl_seconds: int) -> None:
        """
        Record the currently active refresh token for a user.
        Overwrites any previous session, effectively implementing 'session proofing'.
        """
        key = f"{self._prefix}{user_id}"
        self._redis.set(key, jti, ex=ttl_seconds)

    def get_active_refresh_token(self, user_id: str) -> Optional[str]:
        """
        Retrieve the JTI of the currently active refresh token for a user.
        """
        key = f"{self._prefix}{user_id}"
        val = self._redis.get(key)
        return val.decode("utf-8") if val else None

    def invalidate_session(self, user_id: str) -> None:
        """
        Immediately invalidate a user's session by removing their active refresh token record.
        """
        key = f"{self._prefix}{user_id}"
        self._redis.delete(key)

    def is_refresh_token_valid(self, user_id: str, jti: str) -> bool:
        """
        Verify if the provided JTI matches the currently active session for the user.
        """
        active_jti = self.get_active_refresh_token(user_id)
        return active_jti == jti
