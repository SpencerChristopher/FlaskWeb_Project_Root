"""
Article service for orchestrating article lifecycle operations.
Agnostic: No direct DB model imports.
"""

from __future__ import annotations
import datetime
from slugify import slugify

from src.exceptions import ConflictException, NotFoundException, ForbiddenException
from src.events import dispatch_event, article_created, article_deleted, article_updated, article_published
from src.repositories.interfaces import ArticleRepository, UserRepository
from src.schemas import UserIdentity, ArticleCreateUpdate, ArticlePublic


class ArticleService:
    """Application service that encapsulates article domain workflows."""

    def __init__(self, article_repository: ArticleRepository, user_repository: UserRepository):
        self._article_repository = article_repository
        self._user_repository = user_repository

    def _require_ownership_or_admin(self, article, user: UserIdentity, action: str) -> None:
        """Helper to enforce resource ownership with admin override."""
        if user.role == "admin":
            return
        if str(article.author.id) != user.id:
            raise ForbiddenException(f"You do not have permission to {action} this article.")

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
        return self._article_repository.get_published_paginated(page=page, per_page=per_page)

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
        article_slug = slugify(article_dto.title)

        if self._article_repository.get_by_slug(article_slug):
            raise ConflictException("An article with this title already exists")

        # Resolve User model for reference
        author_model = self._user_repository.get_by_id(user.id)
        
        from src.models.article import Article
        
        new_article = Article(
            title=article_dto.title,
            slug=article_slug,
            content=article_dto.content,
            summary=article_dto.summary,
            author=author_model,
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
            user_id=str(created_article.author.id),
        )
        return created_article

    def update_article(
        self,
        article_id: str,
        article_dto: ArticleCreateUpdate,
        user: UserIdentity,
    ):
        article = self.get_article_or_404(article_id)
        self._require_ownership_or_admin(article, user, "update")

        article_slug = slugify(article_dto.title)
        existing = self._article_repository.get_by_slug_excluding_id(article_slug, article_id)
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
