"""
Repository interfaces for persistence access.

These interfaces keep route and service layers decoupled from MongoEngine
query construction details.
"""

from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.comment import Comment
    from src.models.token_blocklist import TokenBlocklist
    from src.models.profile import Profile
    from src.models.article import Article
    from src.schemas import ProfilePublic, ProfileSchema, ArticlePublic, ArticleCreateUpdate


class UserRepository(Protocol):
    """Persistence contract for user lookups and writes."""

    def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    def get_identity(self, user_id: str) -> Optional[User]:
        ...

    def get_by_username(self, username: str) -> Optional[User]:
        ...

    def save(self, user: User) -> User:
        ...

    def delete(self, user: User) -> None:
        ...


class CommentRepository(Protocol):
    """Persistence contract for comment operations."""

    def delete_by_article_id(self, article_id: str) -> int:
        ...

    def save(self, comment: Comment) -> Comment:
        ...


class TokenRepository(Protocol):
    """Persistence contract for token revocation tracking."""

    def is_jti_revoked(self, jti: str) -> bool:
        ...

    def add_to_blocklist(self, jti: str, expires_at: datetime.datetime, ttl: Optional[int] = None) -> None:
        ...


class ProfileRepository(Protocol):
    """Persistence contract for profile operations."""

    def get_profile(self) -> Optional[Profile]:
        ...

    def save(self, profile: Profile) -> Profile:
        ...


class ArticleRepository(Protocol):
    """Persistence contract for article queries and writes."""

    def list_all(self) -> list[Article]:
        ...

    def get_published_paginated(self, page: int, per_page: int):
        ...

    def get_by_id(self, article_id: str) -> Optional[Article]:
        ...

    def get_by_slug(self, slug: str) -> Optional[Article]:
        ...

    def get_by_slug_excluding_id(self, slug: str, article_id: str) -> Optional[Article]:
        ...

    def save(self, article: Article) -> Article:
        ...

    def delete(self, article: Article) -> None:
        ...

# Legacy Aliases for stability
PostRepository = ArticleRepository
