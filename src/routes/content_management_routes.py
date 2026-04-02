"""
Routes for managing content and profile resources.

These endpoints are resource-centric and protected by granular permissions.
They are intended for authenticated administrative or authoring workflows.
"""

from functools import wraps
from typing import Callable, Any

from flask import Blueprint, request, jsonify, Response, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from werkzeug.utils import secure_filename
from src.app.security import permission_required
from src.services import (
    get_authz_service,
    get_article_service,
    get_auth_service,
    get_profile_service,
    get_media_service,
)
from src.services.roles import Permissions
from src.schemas import ArticleCreateUpdate, ProfileSchema
from src.exceptions import UnauthorizedException, BadRequestException

bp = Blueprint("content_management_routes", __name__, url_prefix="/api/content")
authz_service = get_authz_service()
auth_service = get_auth_service()
article_service = get_article_service()
profile_service = get_profile_service()
media_service = get_media_service()


@bp.route("/articles", methods=["GET"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def get_articles() -> Response:
    """List articles for administrative management.

    Returns:
        Response: JSON array of managed article summaries.
    """
    articles = article_service.list_admin_articles(g.current_user)
    return jsonify([article_service.to_public_dict(a) for a in articles]), 200


@bp.route("/articles", methods=["POST"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def create_article() -> Response:
    """Create a new article from a validated payload.

    Returns:
        Response: JSON representation of the created article.

    Raises:
        BadRequestException: If the JSON payload is missing or invalid.
    """
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    article_dto = ArticleCreateUpdate(**data)
    article = article_service.create_article(article_dto, g.current_user)
    return jsonify(article_service.to_public_dict(article)), 201


@bp.route("/articles/<string:article_id>", methods=["GET"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def get_article(article_id: str) -> Response:
    """Retrieve a managed article by its ID.

    Args:
        article_id: The article identifier.

    Returns:
        Response: JSON representation of the article.
    """
    article = article_service.get_article_managed(article_id, g.current_user)
    return jsonify(article_service.to_public_dict(article)), 200


@bp.route("/articles/<string:article_id>", methods=["PUT"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def update_article(article_id: str) -> Response:
    """Update an existing article by ID.

    Args:
        article_id: The article identifier.

    Returns:
        Response: JSON representation of the updated article.

    Raises:
        BadRequestException: If the JSON payload is missing or invalid.
    """
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    article_dto = ArticleCreateUpdate(**data)
    article = article_service.update_article(article_id, article_dto, g.current_user)
    return jsonify(article_service.to_public_dict(article)), 200


@bp.route("/articles/<string:article_id>", methods=["DELETE"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def delete_article(article_id: str) -> Response:
    """Delete an article by ID.

    Args:
        article_id: The article identifier.

    Returns:
        Response: Confirmation message.
    """
    article_service.delete_article(article_id, g.current_user)
    return jsonify({"message": "Article deleted successfully"}), 200


@bp.route("/profile", methods=["GET"])
def get_profile() -> Response:
    """Retrieve the public developer profile singleton.

    Returns:
        Response: JSON representation of the profile.
    """
    profile = profile_service.get_profile()
    return jsonify(profile.model_dump()), 200


@bp.route("/profile", methods=["PUT"])
@permission_required([Permissions.PROFILE_MANAGE])
def update_profile() -> Response:
    """Update the developer profile singleton.

    Returns:
        Response: JSON representation of the updated profile.

    Raises:
        BadRequestException: If the JSON payload is missing or invalid.
    """
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    profile_data = ProfileSchema(**data)
    updated_profile = profile_service.update_profile(profile_data, g.current_user)
    return jsonify(updated_profile.model_dump()), 200


@bp.route("/profile/photo", methods=["POST"])
@permission_required([Permissions.PROFILE_MANAGE])
def upload_profile_photo() -> Response:
    """Replace the profile photo with a newly uploaded image.

    Returns:
        Response: JSON payload containing the new image URL.

    Raises:
        BadRequestException: If the upload is missing or invalid.
    """
    if "file" not in request.files:
        raise BadRequestException("No file part in the request.")

    file = request.files["file"]
    if file.filename == "":
        raise BadRequestException("No selected file.")

    try:
        url = profile_service.update_profile_photo(
            file.stream, file.filename, g.current_user
        )
        return (
            jsonify(
                {
                    "url": url,
                    "message": "Profile photo replaced successfully. Old file deleted.",
                }
            ),
            200,
        )
    except ValueError as e:
        raise BadRequestException(str(e))


@bp.route("/media", methods=["POST"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def upload_media() -> Response:
    """Upload generic media for blog articles.

    Returns:
        Response: JSON payload containing the media URL.

    Raises:
        BadRequestException: If the upload is missing or invalid.
    """
    if "file" not in request.files:
        raise BadRequestException("No file part in the request.")

    file = request.files["file"]
    if file.filename == "":
        raise BadRequestException("No selected file.")

    try:
        url, _file_hash = media_service.save_image(file.stream, file.filename)
        return jsonify({"url": url, "message": "Media uploaded successfully"}), 201
    except ValueError as e:
        raise BadRequestException(str(e))


@bp.route("/media", methods=["DELETE"])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def delete_media() -> Response:
    """Delete a generic media asset by URL.

    Returns:
        Response: Confirmation message.

    Raises:
        BadRequestException: If the URL is missing or deletion fails.
    """
    url = request.args.get("url")
    if not url:
        raise BadRequestException("Missing 'url' parameter.")

    if media_service.delete_image(url):
        return jsonify({"message": "Media deleted successfully"}), 200
    else:
        raise BadRequestException("Failed to delete media or invalid URL.")
