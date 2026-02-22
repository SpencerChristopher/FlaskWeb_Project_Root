"""
Post service for orchestrating post lifecycle operations.
"""

from __future__ import annotations

import datetime

import bleach
from mongoengine.errors import DoesNotExist
from slugify import slugify

from src.exceptions import ConflictException, NotFoundException
from src.events import post_created, post_deleted, post_updated
from src.models.post import Post
from src.models.user import User
from src.repositories.interfaces import PostRepository


class PostService:
    """Application service that encapsulates post domain workflows."""

    def __init__(self, post_repository: PostRepository):
        self._post_repository = post_repository
        self._allowed_tags = [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "code",
            "em",
            "i",
            "li",
            "ol",
            "p",
            "pre",
            "strong",
            "ul",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
        self._allowed_attributes = {
            "a": ["href", "title"],
            "abbr": ["title"],
            "acronym": ["title"],
        }

    def _sanitize_html(self, value: str | None) -> str | None:
        if value is None:
            return None
        return bleach.clean(
            value,
            tags=self._allowed_tags,
            attributes=self._allowed_attributes,
            strip=True,
        )

    def _prepare_for_save(self, post: Post) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        if post.is_published and not post.publication_date:
            post.publication_date = now
        post.last_updated = now
        post.content = self._sanitize_html(post.content) or ""
        post.summary = self._sanitize_html(post.summary)

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
        self._prepare_for_save(new_post)
        created_post = self._post_repository.save(new_post)
        post_created.send(
            created_post,
            post_id=str(created_post.id),
            user_id=str(created_post.author.id),
        )
        return created_post

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
        self._prepare_for_save(post)
        updated_post = self._post_repository.save(post)
        post_updated.send(
            updated_post,
            post_id=str(updated_post.id),
            user_id=str(updated_post.author.id),
            changes={},
        )
        return updated_post

    def delete_post(self, post_id: str) -> None:
        post = self.get_post_or_404(post_id)
        post_author_id = None
        try:
            post_author_id = str(post.author.id)
        except DoesNotExist:
            pass
        persisted_post_id = str(post.id)
        self._post_repository.delete(post)
        if post_author_id:
            post_deleted.send(
                post,
                post_id=persisted_post_id,
                user_id=post_author_id,
            )
