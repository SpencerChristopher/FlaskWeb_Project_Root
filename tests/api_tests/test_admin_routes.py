import re
import pytest
from src.models.user import User
from src.models.post import Post
from flask_jwt_extended import create_access_token
import datetime

# Fixture to create an admin user in the database
@pytest.fixture
def test_admin_user(app):
    with app.app_context():
        admin_user = User(username='adminuser', email='admin@example.com', role='admin')
        admin_user.set_password('AdminPassword123')
        admin_user.save()
        yield admin_user
        admin_user.delete()

# Helper function to log in a user and get tokens
def login_user(client, username, password):
    response = client.post('/api/auth/login', json={
        'username': username,
        'password': password
    })
    assert response.status_code == 200
    
    # Extract access token from Set-Cookie header
    for cookie_header in response.headers.getlist('Set-Cookie'):
        match = re.search(r'access_token_cookie=([^;]+)', cookie_header)
        if match:
            return match.group(1)
    raise Exception("Access token cookie not found in response headers")

# Helper to get admin headers
@pytest.fixture
def admin_headers(client, test_admin_user):
    token = login_user(client, 'adminuser', 'AdminPassword123')
    return {'Authorization': f'Bearer {token}'}

class TestAdminPostRoutes:
    """Tests for admin post management routes."""

    def test_get_post_with_invalid_id_format(self, client, admin_headers):
        """
        Tests that getting a post with an invalid ID format returns a 400 Bad Request.
        This test expects the backend to validate ObjectId format.
        """
        invalid_id = "not-a-valid-objectid"
        response = client.get(f'/api/admin/posts/{invalid_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_update_post_with_invalid_id_format(self, client, admin_headers):
        """
        Tests that updating a post with an invalid ID format returns a 400 Bad Request.
        """
        invalid_id = "another-invalid-id"
        payload = {
            "title": "Updated Title",
            "content": "Updated Content",
            "summary": "Updated Summary",
            "is_published": True
        }
        response = client.put(f'/api/admin/posts/{invalid_id}', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_delete_post_with_invalid_id_format(self, client, admin_headers):
        """
        Tests that deleting a post with an invalid ID format returns a 400 Bad Request.
        """
        invalid_id = "yet-another-invalid-id"
        response = client.delete(f'/api/admin/posts/{invalid_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_get_post_with_nosql_injection_id(self, client, admin_headers):
        """
        Tests that getting a post with a NoSQL injection payload in the ID returns a 400 Bad Request.
        """
        nosql_injection_id = "{'$ne': 'some_value'}" # Example NoSQL injection payload
        response = client.get(f'/api/admin/posts/{nosql_injection_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_update_post_with_nosql_injection_id(self, client, admin_headers):
        """
        Tests that updating a post with a NoSQL injection payload in the ID returns a 400 Bad Request.
        """
        nosql_injection_id = "{'$gt': ''}" # Another example NoSQL injection payload
        payload = {
            "title": "Updated Title",
            "content": "Updated Content",
            "summary": "Updated Summary",
            "is_published": True
        }
        response = client.put(f'/api/admin/posts/{nosql_injection_id}', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_delete_post_with_nosql_injection_id(self, client, admin_headers):
        """
        Tests that deleting a post with a NoSQL injection payload in the ID returns a 400 Bad Request.
        """
        nosql_injection_id = "{'$where': '1 = 1'}" # Yet another example
        response = client.delete(f'/api/admin/posts/{nosql_injection_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    # You would also have tests for valid admin post operations here (create, get, update, delete)
    # For brevity, I'm only adding the new validation tests.
