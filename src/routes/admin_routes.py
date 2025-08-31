"""
This module contains the administrative routes for managing blog posts.

All routes in this module require administrator privileges.
"""

from functools import wraps
from typing import Callable, Any

from flask import Blueprint, request, jsonify, Response, current_app # Removed current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from slugify import slugify
from mongoengine.errors import ValidationError
from pydantic import ValidationError as PydanticValidationError

from src.models.post import Post
from src.models.user import User
from src.schemas import BlogPostCreateUpdate
from src.exceptions import BadRequestException, NotFoundException, ConflictException, ForbiddenException

bp = Blueprint('admin_routes', __name__, url_prefix='/api/admin')

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
        
        if "roles" not in current_user_claims or "admin" not in current_user_claims["roles"]:
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user ID: {current_user_id} "
                f"with roles: {current_user_claims.get('roles', 'N/A')} from IP: {request.remote_addr}"
            )
            raise ForbiddenException("Admin access required.")
        
        # Optionally, fetch the user object if needed in the view function
        # request.current_user = User.objects(id=current_user_id).first()
        
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
    posts = Post.objects()
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

    post_slug = slugify(post_data.title)

    if Post.objects(slug=post_slug).first():
        raise ConflictException("A post with this title already exists")

    current_user_id = get_jwt_identity()
    author_user = User.objects(id=current_user_id).first()
    if not author_user:
        # This case should ideally be caught by admin_required or JWT validation
        raise NotFoundException("Author not found.") 

    new_post = Post(
        title=post_data.title,
        slug=post_slug,
        content=post_data.content,
        summary=post_data.summary,
        author=author_user,
        is_published=post_data.is_published
    )
    try:
        new_post.save()
    except ValidationError as e:
        # Convert MongoEngine validation error to a more structured format
        error_details = {field: message for field, message in e.errors.items()}
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
    post = Post.objects(id=post_id).first()
    if not post:
        raise NotFoundException("Post not found")
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
    post = Post.objects(id=post_id).first()
    if not post:
        raise NotFoundException("Post not found")

    try:
        post_data = BlogPostCreateUpdate(**request.get_json())
    except PydanticValidationError as e:
        raise BadRequestException("Invalid post data", details=e.errors())

    post_slug = slugify(post_data.title)

    # Check if another post with the new slug already exists
    existing_post = Post.objects(slug=post_slug).first()
    if existing_post and str(existing_post.id) != post_id:
        raise ConflictException("A post with this title already exists")

    post.title = post_data.title
    post.slug = post_slug
    post.content = post_data.content
    post.summary = post_data.summary
    post.is_published = post_data.is_published
    try:
        post.save()
    except ValidationError as e:
        # Convert MongoEngine validation error to a more structured format
        error_details = {field: message for field, message in e.errors.items()}
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
    post = Post.objects(id=post_id).first()
    if post:
        post.delete()
        return jsonify({'message': 'Post deleted successfully'}), 200
    else:
        raise NotFoundException("Post not found")



