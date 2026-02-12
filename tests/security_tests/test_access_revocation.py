import pytest
from src.models.user import User


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
    admin_user.role = "user"
    admin_user.save()

    # Old token should no longer grant admin access
    response = client.get("/api/admin/posts", headers=headers)
    assert response.status_code == 403
    data = response.get_json()
    assert data["error_code"] == "FORBIDDEN"


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
