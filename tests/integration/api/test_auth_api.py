import pytest
from src.models.user import User


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username="testuser", email="test@example.com", role="member")
        user.set_password("testpassword")
        user.save()
        yield user
        user.delete()


def test_change_password_successfully(client, test_user, login_user_fixture):
    access_token = login_user_fixture("testuser", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"current_password": "testpassword", "new_password": "NewPassword123!"}
    response = client.post("/api/auth/change-password", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "Password updated successfully"


def test_change_password_with_wrong_current_password(
    client, test_user, login_user_fixture
):
    access_token = login_user_fixture("testuser", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"current_password": "wrongpassword", "new_password": "NewPassword123!"}
    response = client.post("/api/auth/change-password", json=payload, headers=headers)
    assert response.status_code == 401


def test_change_password_with_missing_data(client, test_user, login_user_fixture):
    access_token = login_user_fixture("testuser", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/api/auth/change-password", json={}, headers=headers)
    assert response.status_code == 400
