"""
Post service for orchestrating post lifecycle operations.
"""

from __future__ import annotations

import datetime

import bleach
from mongoengine.errors import DoesNotExist
from slugify import slugify

from src.exceptions import ConflictException, NotFoundException, ForbiddenException
from src.events import dispatch_event, post_created, post_deleted, post_updated, post_published
from src.models.post import Post
from src.models.user import User
from src.repositories.interfaces import PostRepository
from src.schemas import UserIdentity


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

    def _require_ownership_or_admin(self, post: Post, user: UserIdentity, action: str) -> None:
        """Helper to enforce resource ownership with admin override."""
        if user.role == "admin":
            return
        if str(post.author.id) != user.id:
            raise ForbiddenException(f"You do not have permission to {action} this post.")

    def list_admin_posts(self, user: UserIdentity):
        """
        List posts for management view.
        Admins see all posts; others see only their own.
        """
        all_posts = self._post_repository.list_all()
        if user.role == "admin":
            return all_posts
        return [p for p in all_posts if str(p.author.id) == user.id]

    def list_published_posts(self, page: int, per_page: int):
        return self._post_repository.get_published_paginated(page=page, per_page=per_page)

    def get_post_or_404(self, post_id: str) -> Post:
        post = self._post_repository.get_by_id(post_id)
        if not post:
            raise NotFoundException("Post not found")
        return post

    def get_post_managed(self, post_id: str, user: UserIdentity) -> Post:
        """Retrieve a post for management, enforcing ownership."""
        post = self.get_post_or_404(post_id)
        self._require_ownership_or_admin(post, user, "view")
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
        
        # Stage 3: ID-based signaling
        dispatch_event(
            post_created,
            "post_service",
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
        user: UserIdentity,
    ) -> Post:
        post = self.get_post_or_404(post_id)
        self._require_ownership_or_admin(post, user, "update")

        post_slug = slugify(title)

        existing_post = self._post_repository.get_by_slug_excluding_id(post_slug, post_id)
        if existing_post:
            raise ConflictException("A post with this title already exists")

        # Stage 3: Change Tracking
        # Capture old values before they are modified
        old_values = {
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "is_published": post.is_published,
        }

        # Update all fields correctly
        post.title = title
        post.slug = post_slug
        post.content = content
        post.summary = summary
        
        # Check if the post is being newly published
        was_draft = not post.is_published
        post.is_published = is_published

        self._prepare_for_save(post)
        updated_post = self._post_repository.save(post)
        
        # Calculate changes for the signal
        changes = {
            k: {"old": v, "new": getattr(updated_post, k)}
            for k, v in old_values.items()
            if v != getattr(updated_post, k)
        }

        if was_draft and updated_post.is_published:
            dispatch_event(
                post_published,
                "post_service",
                post_id=str(updated_post.id),
                user_id=str(updated_post.author.id),
            )
        elif changes: # Only dispatch post_updated if something actually changed
            dispatch_event(
                post_updated,
                "post_service",
                post_id=str(updated_post.id),
                user_id=str(updated_post.author.id),
                changes=changes,
            )
        return updated_post

    def delete_post(self, post_id: str, user: UserIdentity) -> None:
        post = self.get_post_or_404(post_id)
        self._require_ownership_or_admin(post, user, "delete")

        post_author_id = None
        try:
            post_author_id = str(post.author.id)
        except DoesNotExist:
            pass
        persisted_post_id = str(post.id)
        self._post_repository.delete(post)
        if post_author_id:
            # Stage 3: ID-based signaling
            dispatch_event(
                post_deleted,
                "post_service",
                post_id=persisted_post_id,
                user_id=post_author_id,
            )
