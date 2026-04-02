"""
Service wiring for application-layer orchestration.
"""

from __future__ import annotations
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.auth_service import AuthService
    from src.services.authz_service import AuthzService
    from src.services.article_service import ArticleService
    from src.services.session_service import SessionService
    from src.services.profile_service import ProfileService
    from src.services.media_service import MediaService
    from src.services.turnstile_service import TurnstileService
    from src.services.email_service import EmailService
    from src.services.contact_guard import ContactGuard

_auth_service = None
_authz_service = None
_article_service = None
_session_service = None
_profile_service = None
_media_service = None
_turnstile_service = None
_email_service = None
_contact_guard = None


def _env_flag(name: str, default: str = "false") -> bool:
    value = os.environ.get(name, default)
    return value.strip().lower() in {"1", "true", "yes", "on"}


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


def get_turnstile_service() -> "TurnstileService":
    """Return the singleton Turnstile verification service."""
    global _turnstile_service
    if _turnstile_service is None:
        import os
        from src.services.turnstile_service import TurnstileService

        _turnstile_service = TurnstileService(
            secret_key=os.environ.get("TURNSTILE_SECRET_KEY"),
            enabled=_env_flag("TURNSTILE_ENABLED", "true"),
        )
    return _turnstile_service


def get_email_service() -> "EmailService":
    """Return the singleton SMTP email service."""
    global _email_service
    if _email_service is None:
        import os
        from src.services.email_service import EmailService

        _email_service = EmailService(
            host=os.environ.get("SMTP_HOST"),
            port=int(os.environ.get("SMTP_PORT", "587")),
            username=os.environ.get("SMTP_USER"),
            password=os.environ.get("SMTP_PASSWORD"),
            use_tls=_env_flag("SMTP_USE_TLS", "true"),
            use_ssl=_env_flag("SMTP_USE_SSL", "false"),
            from_email=os.environ.get("CONTACT_FROM_EMAIL"),
            to_email=os.environ.get("CONTACT_TO_EMAIL"),
        )
    return _email_service


def get_contact_guard() -> "ContactGuard":
    """Return the singleton contact guard for bot defense."""
    global _contact_guard
    if _contact_guard is None:
        import os
        from src.services.contact_guard import ContactGuard

        raw_fields = os.environ.get("CONTACT_HONEYPOT_FIELDS", "website,company")
        honeypot_fields = [field.strip() for field in raw_fields.split(",") if field.strip()]

        _contact_guard = ContactGuard(
            min_time_ms=int(os.environ.get("CONTACT_MIN_TIME_MS", "1500")),
            honeypot_fields=honeypot_fields,
        )
    return _contact_guard
