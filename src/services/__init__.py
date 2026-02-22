"""
Service wiring for application-layer orchestration.
"""

from src.repositories import get_post_repository, get_user_repository
from src.services.authz_service import AuthzService
from src.services.post_service import PostService

_authz_service = AuthzService(get_user_repository())
_post_service = PostService(get_post_repository())


def get_authz_service() -> AuthzService:
    return _authz_service


def get_post_service() -> PostService:
    return _post_service
