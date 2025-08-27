import pytest
import json
from src.models.user import User
from src.extensions import db
from flask_jwt_extended import decode_token

# Helper function to get a valid JWT token
def get_jwt_token(client, username, password):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    return data["access_token"]

@pytest.fixture(scope="module", autouse=True)
def setup_users(app):
    """
    Fixture to set up a clean user database for JWT tests.
    Ensures a test admin user exists.
    """
    with app.app_context():
        # Clear users collection
        User.drop_collection()

        # Create a test admin user
        admin_user = User(username="testadmin", email="testadmin@example.com", role="admin")
        admin_user.set_password("testpassword")
        admin_user.save()

        # Create a test regular user
        regular_user = User(username="testuser", email="testuser@example.com", role="user")
        regular_user.set_password("testpassword")
        regular_user.save()

        yield # Provide the setup, then tear down after tests in this module

        # Teardown: Clear users collection after tests
        User.drop_collection()

class TestJWTAuth:
    """Tests for JWT authentication endpoints."""

    def test_successful_admin_login(self, client, setup_users):
        """Test successful login with admin credentials."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testadmin", "password": "testpassword"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "access_token" in data
        assert "refresh_token" in data

        # Decode token and verify claims
        decoded_token = decode_token(data["access_token"])
        assert decoded_token["sub"] is not None
        assert "roles" in decoded_token
        assert "admin" in decoded_token["roles"]

    def test_failed_login_invalid_password(self, client, setup_users):
        """Test login with valid username but invalid password."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testadmin", "password": "wrongpassword"},
            content_type="application/json",
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["message"] == "Invalid username or password"

    def test_failed_login_non_existent_user(self, client, setup_users):
        """Test login with a non-existent username."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "anypassword"},
            content_type="application/json",
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["message"] == "Invalid username or password"

    def test_status_no_token(self, client, setup_users):
        """Test /api/auth/status without a token."""
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["logged_in"] is False

    def test_status_with_valid_token(self, client, setup_users):
        """Test /api/auth/status with a valid token."""
        access_token = get_jwt_token(client, "testadmin", "testpassword")
        response = client.get(
            "/api/auth/status", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["logged_in"] is True
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "admin"

    def test_status_with_invalid_token(self, client, setup_users):
        """Test /api/auth/status with an invalid token."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        response = client.get(
            "/api/auth/status", headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == 422
        data = json.loads(response.data)
        assert "msg" in data # Flask-JWT-Extended's default error message key

    def test_logout_successful(self, client, setup_users):
        """Test successful logout (token is sent, backend confirms)."""
        access_token = get_jwt_token(client, "testadmin", "testpassword")
        response = client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Logged out successfully"

        # After logout, the token should ideally be invalid (if blocklisting is implemented)
        # For now, just check status with the token again - it should still be valid
        # unless blocklisting is active.
        response = client.get(
            "/api/auth/status", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200 # Still 200 because no blocklisting
        assert json.loads(response.data)["logged_in"] is True # Still logged in
