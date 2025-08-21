from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.post import Post
from slugify import slugify
from functools import wraps

bp = Blueprint('admin_routes', __name__, url_prefix='/api/admin')

def admin_required(f):
    """Decorator to ensure user is logged in and is an admin."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # In a real app, you'd check a role, e.g., if not current_user.is_admin:
        # For now, just being logged in is sufficient.
        if not current_user.is_authenticated: # Redundant due to @login_required, but for clarity
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/posts', methods=['GET'])
@admin_required
def get_posts():
    """Gets all posts for the admin dashboard."""
    posts = Post.get_all_posts(current_app.db, published_only=False)
    return jsonify([post.to_dict() for post in posts])

@bp.route('/posts', methods=['POST'])
@admin_required
def create_post():
    """Creates a new post."""
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400

    title = data['title']
    content = data['content']
    is_published = data.get('is_published', False)
    post_slug = slugify(title)

    if Post.get_post_by_slug(current_app.db, post_slug):
        return jsonify({'error': 'A post with this title already exists'}), 409

    new_post_id = Post.create_post(current_app.db, title, post_slug, content, current_user.get_id(), is_published)
    if new_post_id:
        created_post = Post.get_post_by_id(current_app.db, new_post_id)
        return jsonify(created_post), 201
    else:
        return jsonify({'error': 'Failed to create post'}), 500

@bp.route('/posts/<string:post_id>', methods=['GET'])
@admin_required
def get_post(post_id):
    """Gets a single post by its ID."""
    post = Post.get_post_by_id(current_app.db, post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify(post)

@bp.route('/posts/<string:post_id>', methods=['PUT'])
@admin_required
def update_post(post_id):
    """Updates an existing post."""
    if not Post.get_post_by_id(current_app.db, post_id):
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400

    title = data['title']
    post_slug = slugify(title)

    existing_post = Post.get_post_by_slug(current_app.db, post_slug)
    if existing_post and str(existing_post.get('_id')) != post_id:
        return jsonify({'error': 'A post with this title already exists'}), 409

    Post.update_post(
        current_app.db,
        post_id,
        title,
        post_slug,
        data['content'],
        data.get('is_published', False)
    )
    updated_post = Post.get_post_by_id(current_app.db, post_id)
    return jsonify(updated_post), 200

@bp.route('/posts/<string:post_id>', methods=['DELETE'])
@admin_required
def delete_post(post_id):
    """Deletes a post."""
    if Post.delete_post(current_app.db, post_id):
        return jsonify({'message': 'Post deleted successfully'}), 200
    else:
        return jsonify({'error': 'Error deleting post or post not found'}), 404
