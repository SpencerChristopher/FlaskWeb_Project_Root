import pytest
from src.models.user import User
from src.repositories.mongo_user_repository import MongoUserRepository
from src.services.auth_service import AuthService


def test_admin_token_revoked_on_role_downgrade(client, setup_users, login_user_fixture):
    """
    Admin access tokens should become invalid if the user's role is downgraded.
    Expected behavior: admin endpoints reject the request (403).
    """
    # Login as admin to get an access token
    access_token = login_user_fixture("testadmin", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Downgrade the admin user role in the database
    admin_user = User.objects(username="testadmin").first()
    assert admin_user is not None
    auth_service = AuthService(MongoUserRepository())
    auth_service.change_role(user_id=str(admin_user.id), role="user")

    # Old token should no longer grant admin access
    response = client.get("/api/admin/posts", headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error_code"] == "UNAUTHORIZED"


def test_admin_token_revoked_on_user_deletion(client, setup_users, login_user_fixture):
    """
    Admin access tokens should be invalid once the user is deleted.
    Expected behavior: admin endpoints reject the request (401).
    """
    # Login as admin to get an access token
    access_token = login_user_fixture("testadmin", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Delete the admin user from the database
    admin_user = User.objects(username="testadmin").first()
    assert admin_user is not None
    admin_user.delete()

    # Old token should no longer authorize access
    response = client.get("/api/admin/posts", headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error_code"] == "UNAUTHORIZED"


def test_token_revoked_after_role_change_on_status(client, setup_users, login_user_fixture):
    """
    Tokens should be revoked if the user's role changes, even on non-admin endpoints.
    """
    access_token = login_user_fixture("testadmin", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}

    admin_user = User.objects(username="testadmin").first()
    assert admin_user is not None
    auth_service = AuthService(MongoUserRepository())
    auth_service.change_role(user_id=str(admin_user.id), role="user")

    response = client.get("/api/auth/status", headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error_code"] == "UNAUTHORIZED"
