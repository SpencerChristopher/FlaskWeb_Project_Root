"""
Service wiring for application-layer orchestration.
"""

from src.repositories import get_post_repository, get_user_repository
from src.services.auth_service import AuthService
from src.services.authz_service import AuthzService
from src.services.post_service import PostService

_auth_service = AuthService(get_user_repository())
_authz_service = AuthzService(get_user_repository())
_post_service = PostService(get_post_repository())


def get_auth_service() -> AuthService:
    return _auth_service


def get_authz_service() -> AuthzService:
    return _authz_service


def get_post_service() -> PostService:
    return _post_service
