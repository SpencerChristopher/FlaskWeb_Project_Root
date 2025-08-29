import pytest
from src.models.post import Post
from src.models.user import User # Needed for creating posts with authors
import datetime

# Fixture to create a test user (author for posts)
@pytest.fixture
def test_user(app):
    user = User(username='testuser', email='test@example.com', role='user')
    user.set_password('Password123')
    user.save()
    yield user
    user.delete()

# Fixture to create a test post
@pytest.fixture
def test_post(app, test_user):
    post = Post(
        title='Test Post Title',
        slug='test-post-title',
        content='This is the content of the test post.',
        summary='Summary of the test post.',
        author=test_user,
        is_published=True,
        publication_date=datetime.datetime.now(datetime.UTC)
    )
    post.save()
    yield post
    post.delete()

class TestApiRoutes:
    """Tests for public API routes."""

    def test_blog_post_api_with_invalid_slug_format(self, client):
        """
        Tests that requesting a blog post with an invalid slug format returns a 400 Bad Request.
        This test expects the backend to validate slug format.
        """
        invalid_slug = "invalid!slug@"
        response = client.get(f'/api/blog/{invalid_slug}')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Invalid slug format.' in response.json['message']

    def test_blog_post_api_with_nosql_injection_slug(self, client):
        """
        Tests that requesting a blog post with a NoSQL injection payload in the slug returns a 400 Bad Request.
        """
        nosql_injection_slug = "{'$ne': 'some_value'}" # Example NoSQL injection payload
        response = client.get(f'/api/blog/{nosql_injection_slug}')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Invalid slug format.' in response.json['message']

    def test_blog_post_api_with_another_nosql_injection_slug(self, client):
        """
        Tests that requesting a blog post with another NoSQL injection payload in the slug returns a 400 Bad Request.
        """
        nosql_injection_slug = "{'$gt': ''}" # Another example NoSQL injection payload
        response = client.get(f'/api/blog/{nosql_injection_slug}')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Invalid slug format.' in response.json['message']

    def test_blog_list_api_with_invalid_page_param(self, client):
        """
        Tests that requesting blog list with a non-integer page parameter returns a 400 Bad Request.
        """
        response = client.get('/api/blog?page=abc')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Invalid page or per_page parameter' in response.json['message']

    def test_blog_list_api_with_negative_page_param(self, client):
        """
        Tests that requesting blog list with a negative page parameter returns a 400 Bad Request.
        """
        response = client.get('/api/blog?page=-1')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Page and per_page must be positive integers' in response.json['message']

    def test_blog_list_api_with_invalid_per_page_param(self, client):
        """
        Tests that requesting blog list with a non-integer per_page parameter returns a 400 Bad Request.
        """
        response = client.get('/api/blog?per_page=xyz')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Invalid page or per_page parameter' in response.json['message']

    def test_blog_list_api_with_negative_per_page_param(self, client):
        """
        Tests that requesting blog list with a negative per_page parameter returns a 400 Bad Request.
        """
        response = client.get('/api/blog?per_page=-5')
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Page and per_page must be positive integers' in response.json['message']

    def test_blog_post_api_not_found(self, client):
        """Tests that requesting a non-existent blog post returns a 404."""
        response = client.get('/api/blog/non-existent-slug')
        assert response.status_code == 404
        assert response.json['error_code'] == 'NOT_FOUND'
        assert response.json['message'] == 'Post not found'

    def test_blog_post_api_successful(self, client, test_post):
        """Tests that requesting an existing blog post returns it successfully."""
        response = client.get(f'/api/blog/{test_post.slug}')
        assert response.status_code == 200
        assert response.json['title'] == test_post.title
        assert response.json['slug'] == test_post.slug
