"""
Service wiring for application-layer orchestration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.auth_service import AuthService
    from src.services.authz_service import AuthzService
    from src.services.post_service import PostService

_auth_service = None
_authz_service = None
_post_service = None


def get_auth_service() -> "AuthService":
    global _auth_service
    if _auth_service is None:
        from src.repositories import get_user_repository
        from src.services.auth_service import AuthService

        _auth_service = AuthService(get_user_repository())
    return _auth_service


def get_authz_service() -> "AuthzService":
    global _authz_service
    if _authz_service is None:
        from src.repositories import get_user_repository
        from src.services.authz_service import AuthzService

        _authz_service = AuthzService(get_user_repository())
    return _authz_service


def get_post_service() -> "PostService":
    global _post_service
    if _post_service is None:
        from src.repositories import get_post_repository
        from src.services.post_service import PostService

        _post_service = PostService(get_post_repository())
    return _post_service
