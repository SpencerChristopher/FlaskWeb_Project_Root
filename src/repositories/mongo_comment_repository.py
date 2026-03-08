"""
MongoEngine-backed comment repository implementation.
"""

from __future__ import annotations

from pymongo.errors import PyMongoError

from src.exceptions import DatabaseConnectionException
from src.models.comment import Comment
from src.repositories.interfaces import CommentRepository


class MongoCommentRepository(CommentRepository):
    """MongoEngine implementation of comment persistence operations."""

    def delete_by_article_id(self, article_id: str) -> int:
        try:
            return Comment.objects(article=article_id).delete()
        except PyMongoError as e:
            raise DatabaseConnectionException(
                f"Database error while deleting comments for article {article_id}: {e}"
            ) from e

    def save(self, comment: Comment) -> Comment:
        try:
            return comment.save()
        except PyMongoError as e:
            raise DatabaseConnectionException(
                f"Database error while saving comment: {e}"
            ) from e
