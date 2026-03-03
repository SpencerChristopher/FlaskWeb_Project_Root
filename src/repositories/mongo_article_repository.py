"""
MongoEngine-backed article repository implementation.
"""

from __future__ import annotations
from typing import Optional
from pymongo.errors import PyMongoError

from src.exceptions import DatabaseConnectionException
from src.models.article import Article
from src.repositories.interfaces import ArticleRepository


class MongoArticleRepository(ArticleRepository):
    """MongoEngine implementation of article persistence operations."""

    def list_all(self) -> list[Article]:
        try:
            return Article.objects()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while listing all articles: {e}") from e

    def get_published_paginated(self, page: int, per_page: int):
        try:
            return Article.objects(is_published=True).order_by("-publication_date").paginate(
                page=page, per_page=per_page
            )
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching paginated published articles: {e}") from e

    def get_by_id(self, article_id: str) -> Optional[Article]:
        try:
            return Article.objects(id=article_id).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching article by ID: {e}") from e

    def get_by_slug(self, slug: str) -> Optional[Article]:
        try:
            return Article.objects(slug=slug).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching article by slug: {e}") from e

    def get_by_slug_excluding_id(self, slug: str, article_id: str) -> Optional[Article]:
        try:
            return Article.objects(slug=slug, id__ne=article_id).first()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while fetching article by slug excluding ID: {e}") from e

    def save(self, article: Article) -> Article:
        try:
            return article.save()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while saving article: {e}") from e

    def delete(self, article: Article) -> None:
        try:
            article.delete()
        except PyMongoError as e:
            raise DatabaseConnectionException(f"Database error while deleting article: {e}") from e
