"""
MongoEngine-backed post repository implementation.
"""

from __future__ import annotations

from typing import Optional

from src.models.post import Post
from src.repositories.interfaces import PostRepository


from pymongo.errors import PyMongoError
from src.exceptions import DatabaseConnectionException


class MongoPostRepository(PostRepository):
    """MongoEngine implementation of post persistence operations."""

    def list_all(self):
        try:
            return Post.objects()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while listing all posts: {e}") from e

    def get_published_paginated(self, page: int, per_page: int):
        try:
            return Post.objects(is_published=True).order_by("-publication_date").paginate(
                page=page, per_page=per_page
            )
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching paginated published posts: {e}") from e

    def get_by_id(self, post_id: str) -> Optional[Post]:
        try:
            return Post.objects(id=post_id).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching post by ID: {e}") from e

    def get_by_slug(self, slug: str) -> Optional[Post]:
        try:
            return Post.objects(slug=slug).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching post by slug: {e}") from e

    def get_by_slug_excluding_id(self, slug: str, post_id: str) -> Optional[Post]:
        try:
            return Post.objects(slug=slug, id__ne=post_id).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching post by slug excluding ID: {e}") from e

    def save(self, post: Post) -> Post:
        try:
            return post.save()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while saving post: {e}") from e

    def delete(self, post: Post) -> None:
        try:
            post.delete()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while deleting post: {e}") from e
