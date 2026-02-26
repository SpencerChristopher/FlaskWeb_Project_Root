"""
Service wiring for application-layer orchestration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.auth_service import AuthService
    from src.services.authz_service import AuthzService
    from src.services.post_service import PostService
    from src.services.session_service import SessionService
    from src.services.profile_service import ProfileService
    from src.services.media_service import MediaService

_auth_service = None
_authz_service = None
_post_service = None
_session_service = None
_profile_service = None
_media_service = None


def get_session_service() -> "SessionService":
    global _session_service
    if _session_service is None:
        from src.extensions import redis_client
        from src.services.session_service import SessionService

        _session_service = SessionService(redis_client)
    return _session_service


def get_auth_service() -> "AuthService":
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


def get_profile_service() -> "ProfileService":
    global _profile_service
    if _profile_service is None:
        from src.repositories import get_profile_repository
        from src.services.profile_service import ProfileService

        _profile_service = ProfileService(get_profile_repository())
    return _profile_service


def get_media_service() -> "MediaService":
    global _media_service
    if _media_service is None:
        import os
        from src.services.media_service import MediaService

        # Path inside the container
        upload_dir = os.path.join(os.getcwd(), "static", "uploads")
        _media_service = MediaService(upload_dir)
    return _media_service
