"""
This module contains the administrative routes for managing blog posts.

All routes in this module require administrator privileges.
"""

from functools import wraps
from typing import Callable, Any

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from slugify import slugify

from src.models.post import Post
from src.models.user import User

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
            return jsonify({'error': 'Admin access required.'}), 403
        
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
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content') or not data.get('summary'):
        return jsonify({'error': 'Title, content, and summary are required'}), 400

    title = data['title']
    post_slug = slugify(title)

    if Post.objects(slug=post_slug).first():
        return jsonify({'error': 'A post with this title already exists'}), 409

    current_user_id = get_jwt_identity()
    author_user = User.objects(id=current_user_id).first()
    if not author_user:
        return jsonify({'error': 'Author not found.'}), 404 # Should not happen if token is valid

    new_post = Post(
        title=title,
        slug=post_slug,
        content=data['content'],
        summary=data['summary'],
        author=author_user, # Assign the User object
        is_published=data.get('is_published', False)
    )
    new_post.save()
    
    return jsonify(new_post.to_dict()), 201

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
        return jsonify({'error': 'Post not found'}), 404
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
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    if not data or not data.get('title') or not data.get('content') or not data.get('summary'):
        return jsonify({'error': 'Title, content, and summary are required'}), 400

    title = data['title']
    post_slug = slugify(title)

    # Check if another post with the new slug already exists
    existing_post = Post.objects(slug=post_slug).first()
    if existing_post and str(existing_post.id) != post_id:
        return jsonify({'error': 'A post with this title already exists'}), 409

    post.title = title
    post.slug = post_slug
    post.content = data['content']
    post.summary = data['summary']
    post.is_published = data.get('is_published', False)
    post.save()
    
    return jsonify(post.to_dict()), 200

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
        return jsonify({'error': 'Error deleting post or post not found'}), 404
