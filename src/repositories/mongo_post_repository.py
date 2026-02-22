"""
MongoEngine-backed post repository implementation.
"""

from __future__ import annotations

from typing import Optional

from src.models.post import Post
from src.repositories.interfaces import PostRepository


class MongoPostRepository(PostRepository):
    """MongoEngine implementation of post persistence operations."""

    def list_all(self):
        return Post.objects()

    def get_published_paginated(self, page: int, per_page: int):
        return Post.objects(is_published=True).order_by("-publication_date").paginate(
            page=page, per_page=per_page
        )

    def get_by_id(self, post_id: str) -> Optional[Post]:
        return Post.objects(id=post_id).first()

    def get_by_slug(self, slug: str) -> Optional[Post]:
        return Post.objects(slug=slug).first()

    def get_by_slug_excluding_id(self, slug: str, post_id: str) -> Optional[Post]:
        return Post.objects(slug=slug, id__ne=post_id).first()

    def save(self, post: Post) -> Post:
        return post.save()

    def delete(self, post: Post) -> None:
        post.delete()
