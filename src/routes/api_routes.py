"""Public API routes for content, bootstrap data, and contact forms."""

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
    get_turnstile_service,
    get_email_service,
    get_contact_guard,
)

bp = Blueprint("api_routes", __name__, url_prefix="/api")
article_service = get_article_service()
profile_service = get_profile_service()
authz_service = get_authz_service()
auth_service = get_auth_service()
turnstile_service = get_turnstile_service()
email_service = get_email_service()
contact_guard = get_contact_guard()


@bp.route("/bootstrap", methods=["GET"])
@jwt_required(optional=True)
def bootstrap_api() -> Response:
    """Return bootstrap data for the SPA initial load.

    Returns the public profile and (if authenticated) user capabilities.

    Returns:
        Response: JSON payload with profile and auth status.
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
    """Return legacy home payload backed by ProfileService.

    Returns:
        Response: Minimal JSON payload for legacy clients.
    """
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
    """Return the static 'about' section payload.

    Returns:
        Response: JSON content for the about page.
    """
    return jsonify(
        {
            "title": "We've got what you need!",
            "heading": "Spencer's Cooking",
            "description": (
                "Spencer's Cooking is a personal project by me. The goal is to grow "
                "from a professional profile into a searchable recipe hub that helps "
                "you cook more thoughtfully."
            ),
            "mission": (
                "The experience centers on building a recommendation engine that "
                "weighs common ingredients so every weekly meal plan makes shopping "
                "simpler and smarter."
            ),
            "promise": (
                "Every plan is designed so those same ingredients appear in multiple "
                "meals, preventing unfinished jars or produce from lingering in the fridge."
            ),
            "highlights": [
                "Evolve the profile into a recipe knowledge base curated for real life.",
                "Searchable recipes mapped to ingredients you already use.",
                "Personalized weekly plans that reuse every item, cutting waste."
            ],
            "cta_label": "Explore the Blog",
            "cta_link": "/blog",
        }
    )


@bp.route("/blog", methods=["GET"])
def blog_list_api() -> Response:
    """Return the public blog listing with pagination.

    Returns:
        Response: JSON payload of articles and pagination metadata.

    Raises:
        BadRequestException: If page parameters are invalid.
    """
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
            "articles": articles_summary,
            "pagination": {
                "total_articles": paginated_articles.total,
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
    """Return a public article by slug.

    Args:
        slug: URL-safe article slug.

    Returns:
        Response: JSON representation of the article.

    Raises:
        BadRequestException: If the slug format is invalid.
    """
    # Validate slug format using regex
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise BadRequestException("Invalid slug format.")

    article = article_service.get_article_by_slug_or_404(slug)
    return jsonify(article_service.to_public_dict(article))


@bp.route("/license", methods=["GET"])
def license_api() -> Response:
    """Return license information.

    Returns:
        Response: JSON payload with license details.
    """
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


@bp.route("/privacy", methods=["GET"])
def privacy_api() -> Response:
    """Return the privacy policy information.

    Returns:
        Response: JSON payload with privacy policy details.
    """
    return jsonify(
        {
            "title": "Privacy Policy",
            "last_updated": "2026-04-01",
            "sections": [
                {
                    "heading": "Data Sovereignty & GDPR",
                    "content": (
                        "Spencer's Cooking is committed to data privacy and the 'Right to be Forgotten.' "
                        "All data processing is conducted within the EU/UK region."
                    ),
                },
                {
                    "heading": "Data Collection",
                    "content": (
                        "We collect minimal PII: Email (for account identification), "
                        "User Profiles (optional work history), and Comments. "
                        "Standard access logs (IP address, User Agent) are captured by our infrastructure."
                    ),
                },
                {
                    "heading": "Third-Party Processors",
                    "content": (
                        "We use Cloudflare for DDoS protection and Edge security. "
                        "Requests may be processed by Cloudflare's global network according to their privacy policy."
                    ),
                },
                {
                    "heading": "Retention & Deletion",
                    "content": (
                        "Account data is kept until you request deletion via the Security tab in your profile. "
                        "Deleting an account instantly wipes all associated comments and profile data."
                    ),
                },
                {
                    "heading": "Your Rights",
                    "content": (
                        "You have the right to access, rectify, or erase your personal data. "
                        "Contact us if you require a portable export of your data."
                    ),
                },
            ],
        }
    )


@bp.route("/contact", methods=["POST"])
@limiter.limit("5 per minute")
def contact_api() -> Response:
    """Handle contact form submissions with rate limiting.

    Returns:
        Response: Confirmation message.

    Raises:
        BadRequestException: If required fields are missing.
    """
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not all([name, email, message]):
        raise BadRequestException("Name, email, and message are required fields")

    contact_guard.validate(data)

    token = data.get("turnstile_token") or data.get("cf-turnstile-response")
    if turnstile_service.enabled:
        if not token:
            raise BadRequestException("Turnstile token is required.")
        remote_ip = request.headers.get("CF-Connecting-IP") or request.remote_addr
        if not turnstile_service.verify_token(token, remote_ip=remote_ip):
            raise BadRequestException("Turnstile verification failed.")
    else:
        remote_ip = request.headers.get("CF-Connecting-IP") or request.remote_addr

    current_app.logger.info(
        "Contact form submission received from %s (%s), length=%s",
        name,
        email,
        len(message),
    )

    email_service.send_contact_email(
        name=name,
        email=email,
        message=message,
        remote_ip=remote_ip,
        user_agent=request.headers.get("User-Agent"),
    )

    return jsonify({"message": "Message sent successfully!"}), 200
