"""
Repository wiring for persistence access.
"""

from src.repositories.mongo_post_repository import MongoPostRepository
from src.repositories.mongo_user_repository import MongoUserRepository

_user_repository = MongoUserRepository()
_post_repository = MongoPostRepository()


def get_user_repository() -> MongoUserRepository:
    return _user_repository


def get_post_repository() -> MongoPostRepository:
    return _post_repository
