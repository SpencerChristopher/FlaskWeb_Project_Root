from __future__ import annotations
from typing import Optional
from redis import Redis
from redis.exceptions import ConnectionError
from src.exceptions import CacheConnectionException


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
        try:
            self._redis.set(key, jti, ex=ttl_seconds)
        except ConnectionError as e:
            raise CacheConnectionException(f"Cache error while setting active refresh token: {e}") from e

    def get_active_refresh_token(self, user_id: str) -> Optional[str]:
        """
        Retrieve the JTI of the currently active refresh token for a user.
        """
        key = f"{self._prefix}{user_id}"
        try:
            val = self._redis.get(key)
            return val.decode("utf-8") if val else None
        except ConnectionError as e:
            raise CacheConnectionException(f"Cache error while getting active refresh token: {e}") from e

    def invalidate_session(self, user_id: str) -> None:
        """
        Immediately invalidate a user's session by removing their active refresh token record.
        """
        key = f"{self._prefix}{user_id}"
        try:
            self._redis.delete(key)
        except ConnectionError as e:
            raise CacheConnectionException(f"Cache error while invalidating session: {e}") from e

    def is_refresh_token_valid(self, user_id: str, jti: str) -> bool:
        """
        Verify if the provided JTI matches the currently active session for the user.
        """
        try:
            active_jti = self.get_active_refresh_token(user_id)
            return active_jti == jti
        except ConnectionError as e:
            raise CacheConnectionException(f"Cache error while validating refresh token: {e}") from e
