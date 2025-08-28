from flask import Blueprint, jsonify, current_app, request, Response
from src.models.post import Post
from typing import List, Dict, Any
from src.extensions import limiter
from src.exceptions import NotFoundException, BadRequestException
from mongoengine.errors import ValidationError

bp = Blueprint('api_routes', __name__, url_prefix='/api')

@bp.route('/home', methods=['GET'])
def home_api() -> Response:
    return jsonify({
        'title': 'Your Favorite Place for Free Bootstrap Themes',
        'tagline': (
            'Start Bootstrap can help you build better websites using the '
            'Bootstrap framework! Just download a theme and start '
            'customizing, no strings attached!'
        ),
        'button_text': 'Find Out More',
        'button_link': '#about'
    })

@bp.route('/about', methods=['GET'])
def about_api() -> Response:
    return jsonify({
        'title': 'We\'ve got what you need!',
        'content': (
            'Start Bootstrap has everything you need to get your new website '
            'up and running in no time! Choose one of our open source, free '
            'to download, and easy to use themes! No strings attached!'
        ),
        'button_text': 'Get Started!',
        'button_link': '#services'
    })

@bp.route('/blog', methods=['GET'])
def blog_list_api() -> Response:
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 6))
    except (TypeError, ValueError):
        raise BadRequestException("Invalid page or per_page parameter. Must be integers.")

    if page < 1 or per_page < 1:
        raise BadRequestException("Page and per_page must be positive integers.")

    try:
        paginated_posts = Post.objects(is_published=True).order_by(
            '-publication_date'
        ).paginate(page=page, per_page=per_page)
    except ValidationError as e:
        raise NotFoundException(f"Page {page} does not exist.") from e

    posts_summary: List[Dict[str, Any]] = [
        {
            'title': post.title,
            'summary': post.summary,
            'slug': post.slug,
            'publication_date': (
                post.publication_date.strftime('%Y-%m-%d')
                if post.publication_date
                else None
            )
        }
        for post in paginated_posts.items
    ]

    return jsonify({
        'posts': posts_summary,
        'pagination': {
            'total_posts': paginated_posts.total,
            'total_pages': paginated_posts.pages,
            'current_page': paginated_posts.page,
            'per_page': paginated_posts.per_page,
            'has_next': paginated_posts.has_next,
            'has_prev': paginated_posts.has_prev
        }
    })

@bp.route('/blog/<string:slug>', methods=['GET'])
def blog_post_api(slug: str) -> Response:
    post = Post.objects(slug=slug).first()
    if post:
        return jsonify(post.to_dict())
    raise NotFoundException("Post not found")

@bp.route('/license', methods=['GET'])
def license_api() -> Response:
    return jsonify({
        'title': 'License Information',
        'content': (
            'This theme is released under the MIT license. You are free to '
            'use it for any purpose, even commercially. Please see the '
            'LICENSE file for full details.'
        ),
        'copyright': 'Copyright © 2021 - Company Name',
        'distributed_by': 'Themewagon',
        'distributed_by_link': 'https://themewagon.com/'
    })

@bp.route('/contact', methods=['POST'])
@limiter.limit("5 per minute")
def contact_api() -> Response:
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not all([name, email, message]):
        raise BadRequestException("Name, email, and message are required fields")

    current_app.logger.info(
        f"Contact form submission from {name} ({email}): {message}"
    )

    return jsonify({'message': 'Message sent successfully!'}), 200
