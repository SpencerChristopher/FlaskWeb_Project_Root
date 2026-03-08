"""
Service wiring for application-layer orchestration.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.auth_service import AuthService
    from src.services.authz_service import AuthzService
    from src.services.article_service import ArticleService
    from src.services.session_service import SessionService
    from src.services.profile_service import ProfileService
    from src.services.media_service import MediaService

_auth_service = None
_authz_service = None
_article_service = None
_session_service = None
_profile_service = None
_media_service = None


def get_session_service() -> "SessionService":
    """Return the singleton session service instance."""
    global _session_service
    if _session_service is None:
        from src.extensions import redis_client
        from src.services.session_service import SessionService

        _session_service = SessionService(redis_client)
    return _session_service


def get_auth_service() -> "AuthService":
    """Return the singleton auth service instance."""
    global _auth_service
    if _auth_service is None:
        from src.repositories import (
            get_user_repository,
            get_token_repository,
            get_mongo_token_repository,
        )
        from src.services.auth_service import AuthService

        _auth_service = AuthService(
            get_user_repository(),
            get_token_repository(),
            get_mongo_token_repository(),
            get_session_service(),
        )
    return _auth_service


def get_authz_service() -> "AuthzService":
    """Return the singleton authz service instance."""
    global _authz_service
    if _authz_service is None:
        from src.repositories import get_user_repository
        from src.services.authz_service import AuthzService

        _authz_service = AuthzService(get_user_repository())
    return _authz_service


def get_article_service() -> "ArticleService":
    """Return the singleton article service instance."""
    global _article_service
    if _article_service is None:
        from src.repositories import get_article_repository, get_user_repository
        from src.services.article_service import ArticleService

        _article_service = ArticleService(
            get_article_repository(), get_user_repository()
        )
    return _article_service


def get_post_service() -> "ArticleService":
    """Legacy alias for backward compatibility during refactor."""
    return get_article_service()


def get_profile_service() -> "ProfileService":
    """Return the singleton profile service instance."""
    global _profile_service
    if _profile_service is None:
        from src.repositories import get_profile_repository
        from src.services.profile_service import ProfileService

        _profile_service = ProfileService(get_profile_repository(), get_media_service())
    return _profile_service


def get_media_service() -> "MediaService":
    """Return the singleton media service instance."""
    global _media_service
    if _media_service is None:
        import os
        from src.services.media_service import MediaService

        # Path inside the container
        upload_dir = os.path.join(os.getcwd(), "static", "uploads")
        _media_service = MediaService(upload_dir)
    return _media_service
