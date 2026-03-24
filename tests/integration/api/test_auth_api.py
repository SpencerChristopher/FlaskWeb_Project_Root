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


def test_login_requires_turnstile_when_enabled(client, test_user, monkeypatch):
    from src.routes import auth_routes

    class _DummyTurnstile:
        enabled = True

        def verify_token(self, token, remote_ip=None):
            return False

    monkeypatch.setenv("TURNSTILE_LOGIN_ENABLED", "true")
    monkeypatch.setattr(auth_routes, "turnstile_service", _DummyTurnstile())

    response = client.post(
        "/api/auth/login", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 400
