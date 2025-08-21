from flask import Blueprint, jsonify, current_app, request
from app.models.post import Post

bp = Blueprint('api_routes', __name__, url_prefix='/api')

@bp.route('/home', methods=['GET'])
def home_api():
    return jsonify({
        'title': 'Your Favorite Place for Free Bootstrap Themes',
        'tagline': 'Start Bootstrap can help you build better websites using the Bootstrap framework! Just download a theme and start customizing, no strings attached!',
        'button_text': 'Find Out More',
        'button_link': '#about' # This will be handled by frontend routing later
    })

@bp.route('/about', methods=['GET'])
def about_api():
    return jsonify({
        'title': 'We\'ve got what you need!',
        'content': 'Start Bootstrap has everything you need to get your new website up and running in no time! Choose one of our open source, free to download, and easy to use themes! No strings attached!',
        'button_text': 'Get Started!',
        'button_link': '#services' # This will be handled by frontend routing later
    })

@bp.route('/blog', methods=['GET'])
def blog_list_api():
    posts = Post.get_all_posts(current_app.db, published_only=True)
    posts_data = []
    for post in posts:
        posts_data.append({
            'title': post.title,
            'summary': post.summary,
            'slug': post.slug,
            'published_date': post.publication_date.strftime('%Y-%m-%d') if post.publication_date else None
        })
    return jsonify(posts_data)

@bp.route('/blog/<string:slug>', methods=['GET'])
def blog_post_api(slug):
    post = Post.get_post_by_slug(current_app.db, slug)
    if post:
        return jsonify({
            'title': post.title,
            'slug': post.slug,
            'content': post.content,
            'published_date': post.publication_date.strftime('%Y-%m-%d') if post.publication_date else None
        })
    return jsonify({'message': 'Post not found'}), 404

@bp.route('/license', methods=['GET'])
def license_api():
    return jsonify({
        'title': 'License Information',
        'content': 'This theme is released under the MIT license. You are free to use it for any purpose, even commercially. Please see the LICENSE file for full details.',
        'copyright': 'Copyright © 2021 - Company Name',
        'distributed_by': 'Themewagon',
        'distributed_by_link': 'https://themewagon.com/'
    })

@bp.route('/contact', methods=['POST'])
def contact_api():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid JSON'}), 400

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    message = data.get('message')

    # Basic validation
    if not all([name, email, message]):
        return jsonify({'message': 'Name, email, and message are required'}), 400

    # In a real application, you would save this to a database, send an email, etc.
    current_app.logger.info(f"Contact form submission: Name: {name}, Email: {email}, Phone: {phone}, Message: {message}")

    return jsonify({'message': 'Message sent successfully!'}), 200


