"""
Repository wiring for persistence access.
"""

from src.repositories.mongo_article_repository import MongoArticleRepository
from src.repositories.mongo_user_repository import MongoUserRepository
from src.repositories.mongo_comment_repository import MongoCommentRepository
from src.repositories.redis_token_repository import RedisTokenRepository
from src.repositories.mongo_token_repository import MongoTokenRepository
from src.repositories.mongo_profile_repository import MongoProfileRepository
from src.extensions import redis_client

_user_repository = MongoUserRepository()
_article_repository = MongoArticleRepository()
_comment_repository = MongoCommentRepository()
_token_repository = RedisTokenRepository(redis_client)
_mongo_token_repository = MongoTokenRepository()
_profile_repository = MongoProfileRepository()


def get_user_repository() -> MongoUserRepository:
    return _user_repository


def get_article_repository() -> MongoArticleRepository:
    return _article_repository

def get_post_repository() -> MongoArticleRepository:
    """Legacy alias for backward compatibility."""
    return _article_repository


def get_comment_repository() -> MongoCommentRepository:
    return _comment_repository


def get_token_repository() -> RedisTokenRepository:
    return _token_repository


def get_mongo_token_repository() -> MongoTokenRepository:
    return _mongo_token_repository


def get_profile_repository() -> MongoProfileRepository:
    return _profile_repository
