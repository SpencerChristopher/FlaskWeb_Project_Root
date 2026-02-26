"""
Redis-backed token repository implementation for high-performance blocklisting.
"""

from __future__ import annotations

import datetime
from typing import Optional
import redis
from redis.exceptions import RedisError

from src.exceptions import DatabaseConnectionException
from src.repositories.interfaces import TokenRepository


class RedisTokenRepository(TokenRepository):
    """Redis implementation of token blocklist operations."""

    def __init__(self, redis_client: redis.Redis, prefix: str = "revoked_jti:"):
        self._redis = redis_client
        self._prefix = prefix

    def _get_key(self, jti: str) -> str:
        return f"{self._prefix}{jti}"

    def is_jti_revoked(self, jti: str) -> bool:
        try:
            return self._redis.exists(self._get_key(jti)) > 0
        except RedisError as e:
            raise DatabaseConnectionException(f"Redis error while checking token jti={jti}: {e}") from e

    def add_to_blocklist(self, jti: str, expires_at: datetime.datetime, ttl: Optional[int] = None) -> None:
        try:
            key = self._get_key(jti)
            if ttl is None:
                # Calculate TTL based on expiration time if not provided
                delta = expires_at - datetime.datetime.now(datetime.timezone.utc)
                ttl = max(0, int(delta.total_seconds()))
            
            # Store with '1' as value, we only care about existence
            self._redis.setex(key, ttl, "1")
        except RedisError as e:
            raise DatabaseConnectionException(f"Redis error while blocklisting token jti={jti}: {e}") from e
