"""
This module contains routes for managing blog post content.
These routes are resource-centric and enforced by granular permissions.
"""

from functools import wraps
from typing import Callable, Any

from flask import Blueprint, request, jsonify, Response, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from werkzeug.utils import secure_filename
from src.app.security import permission_required
from src.services import get_authz_service, get_post_service, get_auth_service, get_profile_service, get_media_service
from src.services.roles import Permissions
from src.schemas import BlogPostCreateUpdate, ProfileSchema
from src.exceptions import UnauthorizedException, BadRequestException

bp = Blueprint('content_management_routes', __name__, url_prefix='/api/content')
authz_service = get_authz_service()
auth_service = get_auth_service()
post_service = get_post_service()
profile_service = get_profile_service()
media_service = get_media_service()

@bp.route('/posts', methods=['GET'])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def get_posts() -> Response:
    """
    Retrieves posts for management.
    Enforcement: Admins see all; Authors see only own (Handled by Service).
    """
    user_identity = g.current_user
    posts = post_service.list_admin_posts(user_identity)
    return jsonify([post.to_dict() for post in posts])

@bp.route('/posts', methods=['POST'])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def create_post() -> Response:
    """
    Creates a new blog post.
    """
    post_data = BlogPostCreateUpdate(**request.get_json())
    author_user = auth_service.get_user_or_raise(g.current_user.id)

    new_post = post_service.create_post(
        title=post_data.title,
        content=post_data.content,
        summary=post_data.summary,
        is_published=post_data.is_published,
        author=author_user,
    )
    
    response_data = new_post.to_dict()
    response_data['message'] = 'Post created successfully'
    return jsonify(response_data), 201

@bp.route('/posts/<string:post_id>', methods=['GET'])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def get_post(post_id: str) -> Response:
    """
    Retrieves a single post by its unique ID for management.
    Enforcement: Handled by Service.
    """
    post = post_service.get_post_managed(post_id, g.current_user)
    return jsonify(post.to_dict())

@bp.route('/posts/<string:post_id>', methods=['PUT'])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def update_post(post_id: str) -> Response:
    """
    Updates an existing post.
    Enforcement: Handled by Service.
    """
    post_data = BlogPostCreateUpdate(**request.get_json())

    post = post_service.update_post(
        post_id=post_id,
        title=post_data.title,
        content=post_data.content,
        summary=post_data.summary,
        is_published=post_data.is_published,
        user=g.current_user
    )
    
    response_data = post.to_dict()
    response_data['message'] = 'Post updated successfully'
    return jsonify(response_data), 200

@bp.route('/posts/<string:post_id>', methods=['DELETE'])
@permission_required([Permissions.CONTENT_MANAGE, Permissions.CONTENT_AUTHOR])
def delete_post(post_id: str) -> Response:
    """
    Deletes a post.
    Enforcement: Handled by Service.
    """
    post_service.delete_post(post_id, g.current_user)
    return jsonify({'message': 'Post deleted successfully'}), 200


@bp.route('/profile', methods=['GET'])
def get_profile() -> Response:
    """
    Publicly accessible developer profile.
    """
    return jsonify(profile_service.get_profile().model_dump())


@bp.route('/profile', methods=['PUT'])
@permission_required(Permissions.PROFILE_MANAGE)
def update_profile() -> Response:
    """
    Updates the site-wide developer profile.
    """
    profile_data = ProfileSchema(**request.get_json())
    updated_profile = profile_service.update_profile(profile_data)
    return jsonify(updated_profile.model_dump()), 200


@bp.route('/media', methods=['POST'])
@permission_required(Permissions.PROFILE_MANAGE)
def upload_media() -> Response:
    """
    Handles generic image uploads for blog content.
    """
    if 'file' not in request.files:
        raise BadRequestException("No file part in the request.")
    
    file = request.files['file']
    if file.filename == '':
        raise BadRequestException("No selected file.")

    try:
        # Use generic media service for non-singleton assets
        safe_filename = secure_filename(file.filename)
        url = media_service.save_image(file.stream, safe_filename)
        return jsonify({"url": url, "message": "Content image uploaded successfully"}), 201
    except ValueError as e:
        raise BadRequestException(str(e))


@bp.route('/profile/photo', methods=['POST'])
@permission_required(Permissions.PROFILE_MANAGE)
def upload_profile_photo() -> Response:
    """
    Specialized route for updating the singleton profile photo.
    Automatically deletes the old photo from the filesystem.
    """
    if 'file' not in request.files:
        raise BadRequestException("No file part in the request.")
    
    file = request.files['file']
    if file.filename == '':
        raise BadRequestException("No selected file.")

    try:
        safe_filename = secure_filename(file.filename)
        url = profile_service.update_profile_photo(file.stream, safe_filename)
        return jsonify({
            "url": url, 
            "message": "Profile photo replaced successfully. Old file deleted."
        }), 200
    except ValueError as e:
        raise BadRequestException(str(e))



