"""
This module contains the administrative routes for managing blog posts.

All routes in this module require administrator privileges.
"""

from functools import wraps
from typing import Callable, Any

from flask import Blueprint, request, jsonify, Response, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from mongoengine.errors import ValidationError
from pydantic import ValidationError as PydanticValidationError

from src.services import get_authz_service, get_post_service
from src.schemas import BlogPostCreateUpdate
from src.exceptions import BadRequestException, UnauthorizedException

bp = Blueprint('admin_routes', __name__, url_prefix='/api/admin')
authz_service = get_authz_service()
post_service = get_post_service()

def admin_required(f: Callable) -> Callable:
    """
    Decorator to ensure the current user is an authenticated administrator
    with the 'admin' role.

    Args:
        f (Callable): The view function to decorate.

    Returns:
        Callable: The decorated view function.
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        current_user_id = get_jwt_identity()
        current_user_claims = get_jwt()

        g.current_user = authz_service.require_admin(current_user_id, current_user_claims)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/posts', methods=['GET'])
@admin_required
def get_posts() -> Response:
    """
    Retrieves all posts for the admin dashboard, including drafts.

    Returns:
        Response: A JSON array of post objects.
    """
    posts = post_service.list_admin_posts()
    return jsonify([post.to_dict() for post in posts])

@bp.route('/posts', methods=['POST'])
@admin_required
def create_post() -> Response:
    """
    Creates a new blog post.

    Expects a JSON payload with the following keys:
    - 'title' (str): The title of the post.
    - 'content' (str): The main content of the post.
    - 'summary' (str): A short summary for the post list.
    - 'is_published' (bool, optional): The publication status.

    Returns:
        Response: The newly created post object (201) or an error message.
    """
    try:
        post_data = BlogPostCreateUpdate(**request.get_json())
    except PydanticValidationError as e:
        raise BadRequestException("Invalid post data", details=e.errors())

    author_user = getattr(g, "current_user", None)
    if not author_user:
        raise UnauthorizedException("Authentication required or invalid credentials.")

    try:
        new_post = post_service.create_post(
            title=post_data.title,
            content=post_data.content,
            summary=post_data.summary,
            is_published=post_data.is_published,
            author=author_user,
        )
    except ValidationError as e:
        error_map = getattr(e, "errors", None)
        if not isinstance(error_map, dict):
            raise
        # Convert MongoEngine validation error to a more structured format
        error_details = {field: message for field, message in error_map.items()}
        raise BadRequestException("Validation failed", details=error_details)
    
    return jsonify({'message': 'Post created successfully', 'id': str(new_post.id), 'title': new_post.title, 'slug': new_post.slug, 'content': new_post.content, 'summary': new_post.summary, 'is_published': new_post.is_published, 'author': {'id': str(new_post.author.id), 'username': new_post.author.username}}), 201

@bp.route('/posts/<string:post_id>', methods=['GET'])
@admin_required
def get_post(post_id: str) -> Response:
    """
    Retrieves a single post by its unique ID.

    Args:
        post_id (str): The unique identifier of the post.

    Returns:
        Response: The post object if found, or a 404 error.
    """
    post = post_service.get_post_or_404(post_id)
    return jsonify(post.to_dict())

@bp.route('/posts/<string:post_id>', methods=['PUT'])
@admin_required
def update_post(post_id: str) -> Response:
    """
    Updates an existing post.

    Expects a JSON payload with 'title', 'content', and 'summary'.
    Optionally accepts 'is_published'.

    Args:
        post_id (str): The unique identifier of the post to update.

    Returns:
        Response: The updated post object or an error message.
    """
    try:
        post_data = BlogPostCreateUpdate(**request.get_json())
    except PydanticValidationError as e:
        raise BadRequestException("Invalid post data", details=e.errors())

    try:
        post = post_service.update_post(
            post_id=post_id,
            title=post_data.title,
            content=post_data.content,
            summary=post_data.summary,
            is_published=post_data.is_published,
        )
    except ValidationError as e:
        error_map = getattr(e, "errors", None)
        if not isinstance(error_map, dict):
            raise
        # Convert MongoEngine validation error to a more structured format
        error_details = {field: message for field, message in error_map.items()}
        raise BadRequestException("Validation failed", details=error_details)
    
    return jsonify({'message': 'Post updated successfully', 'id': str(post.id), 'title': post.title, 'slug': post.slug, 'content': post.content, 'summary': post.summary, 'is_published': post.is_published, 'author': {'id': str(post.author.id), 'username': post.author.username}}), 200

@bp.route('/posts/<string:post_id>', methods=['DELETE'])
@admin_required
def delete_post(post_id: str) -> Response:
    """
    Deletes a post.

    Args:
        post_id (str): The unique identifier of the post to delete.

    Returns:
        Response: A success message or a 404 error if the post is not found.
    """
    post_service.delete_post(post_id)
    return jsonify({'message': 'Post deleted successfully'}), 200



