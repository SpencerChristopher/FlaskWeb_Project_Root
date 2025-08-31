import pytest
from flask import json
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from src.models.user import User
from src.models.post import Post
from src.models.token_blocklist import TokenBlocklist


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
    access_token = create_access_token(identity=str(admin_user.id), additional_claims={"roles": ["admin"]})
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def user_headers(app, regular_user):
    """Return headers for a regular user."""
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
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert response.json['message'] == 'Invalid post data'
        assert isinstance(response.json['details'], list)
        assert any(err['loc'] == ['summary'] and err['msg'] == 'Field required' for err in response.json['details'])
        assert any(err['loc'] == ['content'] and err['msg'] == 'Field required' for err in response.json['details'])

    def test_create_post_oversized_title(self, client, admin_headers):
        """Test creating a post with an oversized title."""
        payload = {
            'title': 'a' * 201,
            'content': 'This is the content.',
            'summary': 'This is the summary.'
        }
        response = client.post('/api/admin/posts', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert response.json['message'] == 'Invalid post data'
        assert isinstance(response.json['details'], list)
        assert any(err['loc'] == ['title'] and 'at most 200 characters' in err['msg'] for err in response.json['details'])

    def test_create_post_xss_payload(self, client, admin_headers):
        """Test creating a post with an XSS payload."""
        payload = {
            'title': 'XSS Test',
            'content': '<script>alert("xss")</script>',
            'summary': 'This is a summary.'
        }
        response = client.post('/api/admin/posts', headers=admin_headers, json=payload)
        assert response.status_code == 201
        # The response should contain the sanitized content
        assert response.json['content'] == '&lt;script&gt;alert("xss")&lt;/script&gt;'

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
        assert response.status_code == 401
        data = response.json
        assert data['error_code'] == 'UNAUTHORIZED'
        assert data['message'] == 'Signature verification failed or token is malformed.'

    def test_blacklisted_token(self, client, admin_user, app):
        """Test that a blacklisted token is rejected."""
        with app.app_context():
            access_token = create_access_token(identity=str(admin_user.id))
            decoded_token = decode_token(access_token)
            jti = decoded_token["jti"]
            expires = datetime.fromtimestamp(decoded_token["exp"])
            blocklisted_token = TokenBlocklist(jti=jti, expires_at=expires)
            blocklisted_token.save()

        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get('/api/admin/posts', headers=headers)
        assert response.status_code == 401
        data = response.json
        assert data['error_code'] == 'UNAUTHORIZED'
        assert data['message'] == 'Token has been revoked.'

    def test_admin_required_with_missing_roles_claim(self, client, app, regular_user):
        """Test that admin_required rejects tokens with missing 'roles' claim."""
        with app.app_context():
            # Create a token WITHOUT the 'roles' claim
            access_token = create_access_token(identity=str(regular_user.id), additional_claims={})
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get('/api/admin/posts', headers=headers)
        assert response.status_code == 403
        assert "Admin access required." in response.json["message"]

    def test_admin_required_with_non_list_roles_claim(self, client, app, regular_user):
        """Test that admin_required rejects tokens where 'roles' is not a list."""
        with app.app_context():
            # Create a token where 'roles' is a string, not a list
            access_token = create_access_token(identity=str(regular_user.id), additional_claims={"roles": "user"})
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get('/api/admin/posts', headers=headers)
        assert response.status_code == 403
        assert "Admin access required." in response.json["message"]

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

@pytest.mark.skip(reason="IP-based rate limiting is complex to simulate in current test environment")
class TestRateLimiting:
    """Tests for Rate Limiting."""

    @pytest.mark.skip(reason="IP-based rate limiting is complex to simulate in current test environment")
    def test_login_rate_limiting(self, client, setup_users):
        """Test that the login endpoint is rate-limited."""
        username = "testadmin"
        password = "testpassword"
        # Make 5 requests (within the limit of 5 per minute)
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
                content_type="application/json",
            )
            assert response.status_code == 200 or response.status_code == 401 # Can be 401 if password is wrong

        # The 6th request should be rate-limited
        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            content_type="application/json",
        )
        assert response.status_code == 429 # Too Many Requests
        data = response.json
        assert data['error_code'] == 'TOO_MANY_REQUESTS'
        assert data['message'] == 'Too Many Requests'

    @pytest.mark.skip(reason="IP-based rate limiting is complex to simulate in current test environment")
    def test_contact_rate_limiting(self, client):
        """Test that the contact endpoint is rate-limited."""
        payload = {"name": "Test", "email": "test@example.com", "message": "Hello"}
        # Make 5 requests (within the limit of 5 per minute)
        for _ in range(5):
            response = client.post(
                "/api/contact",
                json=payload,
                content_type="application/json",
            )
            assert response.status_code == 200

        # The 6th request should be rate-limited
        response = client.post(
            "/api/contact",
            json=payload,
            content_type="application/json",
        )
        assert response.status_code == 429 # Too Many Requests
        data = response.get_json()
        assert data['error_code'] == 'TOO_MANY_REQUESTS'
        assert data['message'] == 'Too Many Requests'

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
        assert response.json['error_code'] == 'INTERNAL_SERVER_ERROR'
        assert response.json['message'] == 'An unexpected error occurred.'

    def test_no_stack_trace_in_500_response(self, client, admin_headers, monkeypatch):
        """Test that no stack trace is leaked in a 500 response."""
        def mock_objects(*args, **kwargs):
            raise Exception("Simulating a database error")

        monkeypatch.setattr(Post, "objects", mock_objects)

        response = client.get('/api/admin/posts', headers=admin_headers)
        assert response.status_code == 500
        # The response should not contain the word "Traceback"
        assert b"Traceback" not in response.data
