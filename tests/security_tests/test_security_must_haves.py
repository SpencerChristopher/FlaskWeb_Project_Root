
import pytest
from flask import json
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token

from src.models.user import User
from src.models.post import Post
from tests.conftest import client

# --- Fixtures ---

@pytest.fixture
def admin_user(client):
    """Create and return an admin user."""
    user = User(username='testadmin', email='admin@test.com', role='admin')
    user.set_password('password')
    user.save()
    yield user
    user.delete()

@pytest.fixture
def regular_user(client):
    """Create and return a regular user."""
    user = User(username='testuser', email='user@test.com', role='user')
    user.set_password('password')
    user.save()
    yield user
    user.delete()

@pytest.fixture
def admin_headers(app, admin_user):
    """Return headers for an admin user."""
    with app.app_context():
        access_token = create_access_token(identity=str(admin_user.id), additional_claims={"roles": ["admin"]})
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def user_headers(app, regular_user):
    """Return headers for a regular user."""
    with app.app_context():
        access_token = create_access_token(identity=str(regular_user.id), additional_claims={"roles": ["user"]})
    return {'Authorization': f'Bearer {access_token}'}

# --- Security Tests (MUST HAVE) ---

class TestInputValidation:
    """Tests for Input Validation & Sanitization."""

    def test_create_post_invalid_payload(self, client, admin_headers):
        """Test creating a post with an invalid payload."""
        # Missing 'content' and 'summary'
        payload = {'title': 'Invalid Post'}
        response = client.post('/api/admin/posts', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert 'error' in response.json

    def test_create_post_oversized_title(self, client, admin_headers):
        """Test creating a post with an oversized title."""
        payload = {
            'title': 'a' * 201,
            'content': 'This is the content.',
            'summary': 'This is the summary.'
        }
        response = client.post('/api/admin/posts', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert 'error' in response.json

    def test_create_post_xss_payload(self, client, admin_headers):
        """Test creating a post with an XSS payload."""
        payload = {
            'title': 'XSS Test',
            'content': '<script>alert("xss")</script>',
            'summary': 'This is a summary.'
        }
        response = client.post('/api/admin/posts', headers=admin_headers, json=payload)
        assert response.status_code == 201
        # The response should not contain the script tag
        assert '<script>' not in response.json['content']

class TestJWTAuthentication:
    """Tests for JWT Authentication Hardening."""

    def test_access_token_expiry(self, client, admin_user):
        """Test that an expired access token is rejected."""
        with client.application.app_context():
            access_token = create_access_token(
                identity=str(admin_user.id),
                additional_claims={"roles": ["admin"]},
                expires_delta=timedelta(seconds=-1)
            )
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get('/api/admin/posts', headers=headers)
        assert response.status_code == 401

    def test_tampered_token_signature(self, client, admin_headers):
        """Test that a token with a tampered signature is rejected."""
        tampered_token = admin_headers['Authorization'][7:] + 'a'
        headers = {'Authorization': f'Bearer {tampered_token}'}
        response = client.get('/api/admin/posts', headers=headers)
        assert response.status_code == 422  # Invalid token format

    # This test will fail until we implement a token blocklist
    @pytest.mark.xfail(reason="Token blocklist not implemented yet.")
    def test_blacklisted_token(self, client, admin_headers):
        """Test that a blacklisted token is rejected."""
        # 1. Login to get a token
        # 2. Logout to blacklist the token
        # 3. Try to use the blacklisted token
        response = client.post('/api/auth/logout', headers=admin_headers)
        assert response.status_code == 200

        response = client.get('/api/admin/posts', headers=admin_headers)
        assert response.status_code == 401

class TestRBAC:
    """Tests for Role-Based Access Control."""

    def test_admin_can_access_admin_route(self, client, admin_headers):
        """Test that an admin user can access an admin route."""
        response = client.get('/api/admin/posts', headers=admin_headers)
        assert response.status_code == 200

    def test_user_cannot_access_admin_route(self, client, user_headers):
        """Test that a regular user cannot access an admin route."""
        response = client.get('/api/admin/posts', headers=user_headers)
        assert response.status_code == 403

class TestErrorHandlingAndLogging:
    """Tests for Error Handling & Logging."""

    def test_500_error_returns_json(self, client, admin_headers, monkeypatch):
        """Test that a 500 error returns a JSON response."""
        # a 500 error by patching the Post.objects() method to raise an exception
        def mock_objects(*args, **kwargs):
            raise Exception("Simulating a database error")

        monkeypatch.setattr(Post, "objects", mock_objects)

        response = client.get('/api/admin/posts', headers=admin_headers)
        assert response.status_code == 500
        assert response.headers['Content-Type'] == 'application/json'
        assert 'error' in response.json
        assert 'Internal Server Error' in response.json['error']

    def test_no_stack_trace_in_500_response(self, client, admin_headers, monkeypatch):
        """Test that no stack trace is leaked in a 500 response."""
        def mock_objects(*args, **kwargs):
            raise Exception("Simulating a database error")

        monkeypatch.setattr(Post, "objects", mock_objects)

        response = client.get('/api/admin/posts', headers=admin_headers)
        assert response.status_code == 500
        # The response should not contain the word "Traceback"
        assert b"Traceback" not in response.data
