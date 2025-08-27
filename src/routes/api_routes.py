"""
This module defines the public-facing API routes for the application.

These routes do not require authentication and are used to serve content
to the frontend for pages like Home, Blog, About, etc.
"""

from flask import Blueprint, jsonify, current_app, request, Response
from src.models.post import Post
from typing import List, Dict, Any
from src.extensions import limiter # Import limiter
from src.exceptions import NotFoundException, BadRequestException


bp = Blueprint('api_routes', __name__, url_prefix='/api')


@bp.route('/home', methods=['GET'])
def home_api() -> Response:
    """
    Provides static content for the home page.

    Returns:
        Response: A JSON object with title, tagline, and button info.
    """
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
    """
    Provides static content for the About page.

    Returns:
        Response: A JSON object with title, content, and button info.
    """
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
    """
    Retrieves a list of all published blog posts.

    Returns:
        Response: A JSON array of post objects, each a summary.
    """
    posts: List[Post] = Post.objects(is_published=True).order_by(
        '-publication_date'
    )
    # Convert full post objects to a list of summary dictionaries
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
        for post in posts
    ]
    return jsonify(posts_summary)


@bp.route('/blog/<string:slug>', methods=['GET'])
def blog_post_api(slug: str) -> Response:
    """
    Retrieves a single, full-detail blog post by its slug.

    Args:
        slug (str): The URL-friendly slug of the blog post.

    Returns:
        Response: A JSON object of the full blog post or a 404 error.
    """
    post = Post.objects(slug=slug).first()
    if post:
        return jsonify(post.to_dict())
    raise NotFoundException("Post not found")


@bp.route('/license', methods=['GET'])
def license_api() -> Response:
    """
    Provides static content for the license page.

    Returns:
        Response: A JSON object with license and copyright information.
    """
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
@limiter.limit("5 per minute") # Apply rate limit
def contact_api() -> Response:
    """
    Handles contact form submissions. This is a mock endpoint.

    In a real application, this would handle sending an email or saving
    the message to a database.

    Expects a JSON payload with:
    - 'name' (str)
    - 'email' (str)
    - 'message' (str)
    - 'phone' (str, optional)

    Returns:
        Response: A success or error message.
    """
    data = request.get_json()
    if not data:
        raise BadRequestException("Invalid JSON payload")

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not all([name, email, message]):
        raise BadRequestException("Name, email, and message are required fields")

    # Log the submission for demonstration purposes
    current_app.logger.info(
        f"Contact form submission from {name} ({email}): {message}"
    )

    return jsonify({'message': 'Message sent successfully!'}), 200