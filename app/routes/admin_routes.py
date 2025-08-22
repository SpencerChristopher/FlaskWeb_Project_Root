"""
This module contains the administrative routes for managing blog posts.

All routes in this module require administrator privileges.
"""

from functools import wraps
from typing import Callable, Any

from flask import Blueprint, request, jsonify, current_app, Response
from flask_login import login_required, current_user
from slugify import slugify

from app.models.post import Post

bp = Blueprint('admin_routes', __name__, url_prefix='/api/admin')

def admin_required(f: Callable) -> Callable:
    """
    Decorator to ensure the current user is an authenticated administrator.

    For this application, any authenticated user is considered an admin.
    In a real-world scenario, this would check for a specific role or permission.

    Args:
        f (Callable): The view function to decorate.

    Returns:
        Callable: The decorated view function.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Admin access required.'}), 403
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
    posts = Post.get_all_posts(current_app.db, published_only=False)
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

    if Post.get_post_by_slug(current_app.db, post_slug):
        return jsonify({'error': 'A post with this title already exists'}), 409

    new_post_id = Post.create_post(
        db=current_app.db,
        title=title,
        slug=post_slug,
        content=data['content'],
        summary=data['summary'],
        author_id=current_user.get_id(),
        is_published=data.get('is_published', False)
    )
    
    if new_post_id:
        created_post = Post.get_post_by_id(current_app.db, str(new_post_id))
        if created_post:
            return jsonify(created_post.to_dict()), 201
    
    return jsonify({'error': 'Failed to create post'}), 500

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
    post = Post.get_post_by_id(current_app.db, post_id)
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
    post = Post.get_post_by_id(current_app.db, post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    if not data or not data.get('title') or not data.get('content') or not data.get('summary'):
        return jsonify({'error': 'Title, content, and summary are required'}), 400

    title = data['title']
    post_slug = slugify(title)

    # Check if another post with the new slug already exists
    existing_post = Post.get_post_by_slug(current_app.db, post_slug)
    if existing_post and str(existing_post._id) != post_id:
        return jsonify({'error': 'A post with this title already exists'}), 409

    modified_count = Post.update_post(
        db=current_app.db,
        post_id=post_id,
        title=title,
        slug=post_slug,
        content=data['content'],
        summary=data['summary'],
        is_published=data.get('is_published', False)
    )
    
    if modified_count > 0:
        updated_post = Post.get_post_by_id(current_app.db, post_id)
        if updated_post:
            return jsonify(updated_post.to_dict()), 200
    
    return jsonify({'error': 'Failed to update post or no changes made'}), 500

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
    if Post.delete_post(current_app.db, post_id):
        return jsonify({'message': 'Post deleted successfully'}), 200
    else:
        return jsonify({'error': 'Error deleting post or post not found'}), 404
