"""
Repository wiring for persistence access.
"""

from src.repositories.mongo_post_repository import MongoPostRepository
from src.repositories.mongo_user_repository import MongoUserRepository
from src.repositories.mongo_comment_repository import MongoCommentRepository
from src.repositories.redis_token_repository import RedisTokenRepository
from src.repositories.mongo_token_repository import MongoTokenRepository
from src.extensions import redis_client

_user_repository = MongoUserRepository()
_post_repository = MongoPostRepository()
_comment_repository = MongoCommentRepository()
_token_repository = RedisTokenRepository(redis_client)
_mongo_token_repository = MongoTokenRepository()


def get_user_repository() -> MongoUserRepository:
    return _user_repository


def get_post_repository() -> MongoPostRepository:
    return _post_repository


def get_comment_repository() -> MongoCommentRepository:
    return _comment_repository


def get_token_repository() -> RedisTokenRepository:
    return _token_repository


def get_mongo_token_repository() -> MongoTokenRepository:
    return _mongo_token_repository
