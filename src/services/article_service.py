"""
Article service for orchestrating article lifecycle operations.
Agnostic: No direct DB model imports.
"""

from __future__ import annotations
import datetime
from slugify import slugify

from src.exceptions import (
    ConflictException,
    NotFoundException,
    ForbiddenException,
    UnauthorizedException,
)
from src.events import (
    dispatch_event,
    article_created,
    article_deleted,
    article_updated,
    article_published,
)
from src.repositories.interfaces import ArticleRepository, UserRepository
from src.schemas import UserIdentity, ArticleCreateUpdate, ArticlePublic


class ArticleService:
    """Application service that encapsulates article domain workflows."""

    def __init__(
        self, article_repository: ArticleRepository, user_repository: UserRepository
    ):
        self._article_repository = article_repository
        self._user_repository = user_repository

    def _require_ownership_or_admin(
        self, article, user: UserIdentity, action: str
    ) -> None:
        """Helper to enforce resource ownership with admin override."""
        if user.role == "admin":
            return
        if not getattr(article, "author", None):
            raise NotFoundException("Article not found")
        if str(article.author.id) != user.id:
            raise ForbiddenException(
                f"You do not have permission to {action} this article."
            )

    def list_admin_articles(self, user: UserIdentity):
        """
        List articles for management view.
        Admins see all articles; others see only their own.
        """
        all_articles = self._article_repository.list_all()
        if user.role == "admin":
            return all_articles
        return [a for a in all_articles if str(a.author.id) == user.id]

    def list_published_articles(self, page: int, per_page: int):
        """
        Retrieves a paginated list of published articles for public consumption.

        Logic:
        1. Filters by is_published=True.
        2. Projects only necessary fields for performance (via Repository).
        3. Orders by publication_date descending.

        Args:
            page (int): The page number to retrieve.
            per_page (int): The number of items per page.

        Returns:
            Pagination: A MongoEngine pagination object containing Article models.
        """
        return self._article_repository.get_published_paginated(
            page=page, per_page=per_page
        )

    def to_public_dict(self, article) -> dict:
        """
        Maps a persisted Article model to the ArticlePublic DTO.
        
        This stabilizes the API shape by ensuring internal model changes 
        don't leak to the frontend. It converts MongoEngine IDs to strings 
        and formats date fields.

        Args:
            article (Article): The persisted article model instance.

        Returns:
            dict: The serialized public article data validated by ArticlePublic.
        """
        return ArticlePublic(
            id=str(article.id),
            title=article.title,
            summary=article.summary or "",
            content=article.content,
            slug=article.slug,
            is_published=article.is_published,
            publication_date=(
                article.publication_date.isoformat()
                if article.publication_date
                else None
            ),
            last_updated=(
                article.last_updated.isoformat() if article.last_updated else None
            ),
            author_username=article.author.username if article.author else None,
        ).model_dump()

    def to_list_dict(self, article) -> dict:
        """Map a persisted article to the public list DTO used by the blog index."""
        return {
            "title": article.title,
            "summary": article.summary or "",
            "slug": article.slug,
            "publication_date": (
                article.publication_date.isoformat()
                if article.publication_date
                else None
            ),
        }

    def get_article_or_404(self, article_id: str):
        article = self._article_repository.get_by_id(article_id)
        if not article:
            raise NotFoundException("Article not found")
        return article

    def get_article_managed(self, article_id: str, user: UserIdentity):
        """Retrieve an article for management, enforcing ownership."""
        article = self.get_article_or_404(article_id)
        self._require_ownership_or_admin(article, user, "view")
        return article

    def get_article_by_slug_or_404(self, slug: str):
        article = self._article_repository.get_by_slug(slug)
        if not article:
            raise NotFoundException("Article not found")
        return article

    def create_article(
        self,
        article_dto: ArticleCreateUpdate,
        user: UserIdentity,
    ):
        """
        Orchestrates the creation of a new article.

        Logic:
        1. Generates a URL-safe slug from the title.
        2. Checks for slug collisions (ConflictException).
        3. Assigns ownership to the current user (using lazy proxy).
        4. Sets publication date if is_published=True.
        5. Dispatches 'article_created' signal on success.

        Args:
            article_dto (ArticleCreateUpdate): Validated data transfer object.
            user (UserIdentity): Identity of the user creating the article.

        Returns:
            Article: The persisted article instance.

        Raises:
            ConflictException: If an article with the same slug already exists.
        """
        article_slug = slugify(article_dto.title)

        if self._article_repository.get_by_slug(article_slug):
            raise ConflictException("An article with this title already exists")

        # Optimization: Use a lazy reference instead of a full DB fetch.
        # MongoEngine allows assigning the ID string directly to a ReferenceField.
        from src.models.article import Article

        new_article = Article(
            title=article_dto.title,
            slug=article_slug,
            content=article_dto.content,
            summary=article_dto.summary,
            author=user.id,  # MongoEngine handles ID-to-Proxy assignment
            is_published=article_dto.is_published,
        )

        # Handle Publication Logic
        now = datetime.datetime.now(datetime.timezone.utc)
        if new_article.is_published:
            new_article.publication_date = now
        new_article.last_updated = now

        created_article = self._article_repository.save(new_article)

        dispatch_event(
            article_created,
            "article_service",
            article_id=str(created_article.id),
            user_id=user.id,
        )
        return created_article

    def update_article(
        self,
        article_id: str,
        article_dto: ArticleCreateUpdate,
        user: UserIdentity,
    ):
        """
        Updates an existing article, enforcing ownership and handling state transitions.

        Logic:
        1. Verifies article existence and ownership/admin permission.
        2. Checks if the new title creates a slug collision with a different article.
        3. Updates fields and handles publication timestamping (draft -> published).
        4. Dispatches 'article_published' if status changed, otherwise 'article_updated'.

        Args:
            article_id (str): The ID of the article to update.
            article_dto (ArticleCreateUpdate): The new data for the article.
            user (UserIdentity): Identity of the user performing the update.

        Returns:
            Article: The updated and persisted article instance.

        Raises:
            NotFoundException: If the article does not exist.
            ForbiddenException: If the user lacks permission.
            ConflictException: If the new title/slug is taken by another article.
        """
        article = self.get_article_or_404(article_id)
        self._require_ownership_or_admin(article, user, "update")

        article_slug = slugify(article_dto.title)
        existing = self._article_repository.get_by_slug_excluding_id(
            article_slug, article_id
        )
        if existing:
            raise ConflictException("An article with this title already exists")

        # Update fields
        article.title = article_dto.title
        article.slug = article_slug
        article.content = article_dto.content
        article.summary = article_dto.summary

        was_draft = not article.is_published
        article.is_published = article_dto.is_published

        now = datetime.datetime.now(datetime.timezone.utc)
        if article.is_published and not article.publication_date:
            article.publication_date = now
        article.last_updated = now

        updated_article = self._article_repository.save(article)

        if was_draft and updated_article.is_published:
            dispatch_event(
                article_published,
                "article_service",
                article_id=str(updated_article.id),
                user_id=str(updated_article.author.id),
            )
        else:
            dispatch_event(
                article_updated,
                "article_service",
                article_id=str(updated_article.id),
                user_id=str(updated_article.author.id),
            )
        return updated_article

    def delete_article(self, article_id: str, user: UserIdentity) -> None:
        """
        Deletes an article and dispatches cleanup signals.

        Logic:
        1. Verifies article existence and ownership/admin permission.
        2. Deletes the document from the 'posts' collection.
        3. Dispatches 'article_deleted' signal to trigger comment and media cleanup.

        Args:
            article_id (str): The ID of the article to delete.
            user (UserIdentity): Identity of the user performing the deletion.

        Raises:
            NotFoundException: If the article does not exist.
            ForbiddenException: If the user lacks permission.
        """
        article = self.get_article_or_404(article_id)
        self._require_ownership_or_admin(article, user, "delete")

        author_id = str(article.author.id)
        persisted_id = str(article.id)
        self._article_repository.delete(article)

        dispatch_event(
            article_deleted,
            "article_service",
            article_id=persisted_id,
            user_id=author_id,
        )
