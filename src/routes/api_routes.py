"""Public API routes for content and contact."""

import re
from flask import Blueprint, jsonify, current_app, request, Response
from typing import List, Dict, Any
from src.extensions import limiter
from src.exceptions import BadRequestException
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.services import (
    get_article_service,
    get_profile_service,
    get_authz_service,
    get_auth_service,
)

bp = Blueprint("api_routes", __name__, url_prefix="/api")
article_service = get_article_service()
profile_service = get_profile_service()
authz_service = get_authz_service()
auth_service = get_auth_service()


@bp.route("/bootstrap", methods=["GET"])
@jwt_required(optional=True)
def bootstrap_api() -> Response:
    """
    Combined endpoint for initial app load.
    Returns the public profile AND current auth status.
    """
    profile = profile_service.get_profile()

    auth_status = {"logged_in": False}
    current_user_id = get_jwt_identity()
    if current_user_id:
        user = auth_service.get_user(current_user_id)
        if user:
            auth_status = {
                "logged_in": True,
                "user": {
                    "username": user.username,
                    "capabilities": authz_service.get_user_capabilities(get_jwt()),
                },
            }

    return jsonify({"profile": profile.model_dump(), "auth": auth_status}), 200


@bp.route("/home", methods=["GET"])
def home_api() -> Response:
    """Legacy/Simple home data endpoint, now backed by ProfileService."""
    profile = profile_service.get_profile()
    return jsonify(
        {
            "title": profile.name,
            "tagline": profile.statement,
            "button_text": "Technical Blog",
            "button_link": "/blog",
        }
    )


@bp.route("/about", methods=["GET"])
def about_api() -> Response:
    """Return 'about' section data."""
    return jsonify(
        {
            "title": "We've got what you need!",
            "content": (
                "Start Bootstrap has everything you need to get your new website "
                "up and running in no time! Choose one of our open source, free "
                "to download, and easy to use themes! No strings attached!"
            ),
            "button_text": "Get Started!",
            "button_link": "/services",
        }
    )


@bp.route("/blog", methods=["GET"])
def blog_list_api() -> Response:
    """Public blog listing (still uses /blog for SEO/URLs)."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 6))
    except (TypeError, ValueError):
        raise BadRequestException(
            "Invalid page or per_page parameter. Must be integers."
        )

    if page < 1 or per_page < 1:
        raise BadRequestException("Page and per_page must be positive integers.")

    paginated_articles = article_service.list_published_articles(
        page=page, per_page=per_page
    )

    articles_summary: List[Dict[str, Any]] = [
        article_service.to_list_dict(article) for article in paginated_articles.items
    ]

    return jsonify(
        {
            "posts": articles_summary,
            "pagination": {
                "total_posts": paginated_articles.total,
                "total_pages": paginated_articles.pages,
                "current_page": paginated_articles.page,
                "per_page": paginated_articles.per_page,
                "has_next": paginated_articles.has_next,
                "has_prev": paginated_articles.has_prev,
            },
        }
    )


@bp.route("/blog/<string:slug>", methods=["GET"])
def blog_article_api(slug: str) -> Response:
    """Public article view."""
    # Validate slug format using regex
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise BadRequestException("Invalid slug format.")

    article = article_service.get_article_by_slug_or_404(slug)
    return jsonify(article_service.to_public_dict(article))


@bp.route("/license", methods=["GET"])
def license_api() -> Response:
    """Return 'license' information."""
    return jsonify(
        {
            "title": "License Information",
            "content": (
                "This theme is released under the MIT license. You are free to "
                "use it for any purpose, even commercially. Please see the "
                "LICENSE file for full details."
            ),
            "copyright": "Copyright © 2021 - Company Name",
            "distributed_by": "Themewagon",
            "distributed_by_link": "https://themewagon.com/",
        }
    )


@bp.route("/contact", methods=["POST"])
@limiter.limit("5 per minute")
def contact_api() -> Response:
    """Handle contact form submissions."""
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not all([name, email, message]):
        raise BadRequestException("Name, email, and message are required fields")

    current_app.logger.info(f"Contact form submission from {name} ({email}): {message}")

    return jsonify({"message": "Message sent successfully!"}), 200
