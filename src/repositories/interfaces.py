"""
Repository interfaces for persistence access.

These interfaces keep route and service layers decoupled from MongoEngine
query construction details.
"""

from __future__ import annotations

from typing import Optional, Protocol

from src.models.post import Post
from src.models.user import User


class UserRepository(Protocol):
    """Persistence contract for user lookups and writes."""

    def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    def get_by_username(self, username: str) -> Optional[User]:
        ...

    def save(self, user: User) -> User:
        ...

    def delete(self, user: User) -> None:
        ...


class PostRepository(Protocol):
    """Persistence contract for post queries and writes."""

    def list_all(self):
        ...

    def get_published_paginated(self, page: int, per_page: int):
        ...

    def get_by_id(self, post_id: str) -> Optional[Post]:
        ...

    def get_by_slug(self, slug: str) -> Optional[Post]:
        ...

    def get_by_slug_excluding_id(self, slug: str, post_id: str) -> Optional[Post]:
        ...

    def save(self, post: Post) -> Post:
        ...

    def delete(self, post: Post) -> None:
        ...
