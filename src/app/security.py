"""
Security and auth configuration helpers for the Flask app factory.
"""

import datetime
import os

from flask import Flask
from flask_cors import CORS
from flask_talisman import Talisman

from src.exceptions import UnauthorizedException
from src.extensions import jwt, limiter
from src.repositories import get_user_repository


def register_jwt_loaders(jwt_manager) -> None:
    """Register JWT callback handlers."""

    @jwt_manager.unauthorized_loader
    def unauthorized_response(callback_exception):
        return UnauthorizedException("Missing or invalid token.").to_dict(), 401

    @jwt_manager.invalid_token_loader
    def invalid_token_response(callback_exception):
        return UnauthorizedException("Signature verification failed or token is malformed.").to_dict(), 401

    @jwt_manager.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return UnauthorizedException("Token has been revoked.").to_dict(), 401

    @jwt_manager.needs_fresh_token_loader
    def needs_fresh_token_response(callback_exception):
        return UnauthorizedException("Fresh token required.").to_dict(), 401


def configure_http_security(app: Flask) -> None:
    """Configure Talisman and extra response security headers."""
    app_env = os.environ.get("FLASK_ENV", "development")
    csp = {
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
        ],
        "style-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://fonts.googleapis.com",
            "'unsafe-inline'",
        ],
        "font-src": [
            "https://fonts.gstatic.com",
            "https://cdn.jsdelivr.net",
        ],
        "img-src": "*",
    }

    talisman_kwargs = {
        "content_security_policy": csp,
        "content_security_policy_nonce_in": ["script-src"],
        "referrer_policy": "strict-origin-when-cross-origin",
    }

    if app_env == "production":
        talisman_kwargs["strict_transport_security"] = True
        talisman_kwargs["strict_transport_security_max_age"] = 31536000
        talisman_kwargs["strict_transport_security_include_subdomains"] = True
        force_https = os.environ.get("TALISMAN_FORCE_HTTPS", "true").lower() == "true"
        talisman_kwargs["force_https"] = force_https
    else:
        report_uri = os.environ.get("CSP_REPORT_URI")
        if report_uri:
            talisman_kwargs["content_security_policy_report_only"] = True
            talisman_kwargs["content_security_policy_report_uri"] = report_uri
        talisman_kwargs["force_https"] = False

    Talisman(app, **talisman_kwargs)

    @app.after_request
    def add_extra_security_headers(response):
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


def configure_cors(app: Flask) -> None:
    """Configure API CORS from environment list."""
    cors_origins = os.environ.get("CORS_ORIGINS", "")
    if cors_origins:
        allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    else:
        allowed_origins = []
    if allowed_origins:
        CORS(
            app,
            resources={r"/api/*": {"origins": allowed_origins}},
            supports_credentials=True,
        )


def configure_jwt(app: Flask) -> None:
    """Configure JWT extension, token callbacks, and cookie/token settings."""
    app.config["JWT_SECRET_KEY"] = os.environ.get("SECRET_KEY")
    jwt.init_app(app)
    register_jwt_loaders(jwt)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from src.services import get_auth_service

        auth_service = get_auth_service()
        return auth_service.is_token_revoked(jwt_payload)

    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_SECURE"] = os.environ.get("JWT_COOKIE_SECURE", "true").lower() == "true"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = os.environ.get("JWT_COOKIE_CSRF_PROTECT", "true").lower() == "true"
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
    app.config["JWT_REFRESH_COOKIE_PATH"] = "/api/auth/refresh"
    app.config["JWT_COOKIE_SAMESITE"] = os.environ.get("JWT_COOKIE_SAMESITE", "Lax")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=7)


def configure_rate_limiter(app: Flask) -> None:
    """Initialize Flask-Limiter on the current app."""
    limiter.init_app(app)
