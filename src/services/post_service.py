"""
Post service for orchestrating post lifecycle operations.
"""

from __future__ import annotations

from slugify import slugify

from src.exceptions import ConflictException, NotFoundException
from src.models.post import Post
from src.models.user import User
from src.repositories.interfaces import PostRepository


class PostService:
    """Application service that encapsulates post domain workflows."""

    def __init__(self, post_repository: PostRepository):
        self._post_repository = post_repository

    def list_admin_posts(self):
        return self._post_repository.list_all()

    def list_published_posts(self, page: int, per_page: int):
        return self._post_repository.get_published_paginated(page=page, per_page=per_page)

    def get_post_or_404(self, post_id: str) -> Post:
        post = self._post_repository.get_by_id(post_id)
        if not post:
            raise NotFoundException("Post not found")
        return post

    def get_post_by_slug_or_404(self, slug: str) -> Post:
        post = self._post_repository.get_by_slug(slug)
        if not post:
            raise NotFoundException("Post not found")
        return post

    def create_post(
        self,
        *,
        title: str,
        content: str,
        summary: str,
        is_published: bool,
        author: User,
    ) -> Post:
        post_slug = slugify(title)

        if self._post_repository.get_by_slug(post_slug):
            raise ConflictException("A post with this title already exists")

        new_post = Post(
            title=title,
            slug=post_slug,
            content=content,
            summary=summary,
            author=author,
            is_published=is_published,
        )
        return self._post_repository.save(new_post)

    def update_post(
        self,
        *,
        post_id: str,
        title: str,
        content: str,
        summary: str,
        is_published: bool,
    ) -> Post:
        post = self.get_post_or_404(post_id)
        post_slug = slugify(title)

        existing_post = self._post_repository.get_by_slug_excluding_id(post_slug, post_id)
        if existing_post:
            raise ConflictException("A post with this title already exists")

        post.title = title
        post.slug = post_slug
        post.content = content
        post.summary = summary
        post.is_published = is_published
        return self._post_repository.save(post)

    def delete_post(self, post_id: str) -> None:
        post = self.get_post_or_404(post_id)
        self._post_repository.delete(post)
