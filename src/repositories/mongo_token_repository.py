"""
MongoEngine-backed token repository implementation for blocklisting.
"""

from __future__ import annotations

import datetime
from pymongo.errors import PyMongoError

from src.exceptions import DatabaseConnectionException
from src.models.token_blocklist import TokenBlocklist
from src.repositories.interfaces import TokenRepository


class MongoTokenRepository(TokenRepository):
    """MongoEngine implementation of token blocklist operations."""

    def is_jti_revoked(self, jti: str) -> bool:
        try:
            return TokenBlocklist.objects(jti=jti).first() is not None
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while checking token jti={jti}: {e}") from e

    def add_to_blocklist(self, jti: str, expires_at: datetime.datetime) -> None:
        try:
            TokenBlocklist(jti=jti, expires_at=expires_at).save()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while blocklisting token jti={jti}: {e}") from e
