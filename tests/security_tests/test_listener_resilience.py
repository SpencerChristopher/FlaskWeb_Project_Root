from src.events import user_deleted, user_logged_in
from src.models.user import User
from src.repositories.mongo_user_repository import MongoUserRepository
from src.services.auth_service import AuthService


def test_login_succeeds_when_login_listener_fails(client, app):
    with app.app_context():
        user = User(
            username="listener_login_user",
            email="listener_login_user@example.com",
            role="user",
        )
        user.set_password("Password123!")
        user.save()

    def failing_listener(sender, **kwargs):
        raise RuntimeError("simulated listener failure")

    user_logged_in.connect(failing_listener, weak=False)
    try:
        response = client.post(
            "/api/auth/login",
            json={"username": "listener_login_user", "password": "Password123!"},
        )
        assert response.status_code == 200
    finally:
        user_logged_in.disconnect(failing_listener)


def test_revocation_still_works_when_user_deleted_listener_fails(
    client, setup_users, login_user_fixture
):
    access_token = login_user_fixture("testadmin", "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}

    def failing_listener(sender, **kwargs):
        raise RuntimeError("simulated user_deleted listener failure")

    user_deleted.connect(failing_listener, weak=False)
    try:
        admin_user = User.objects(username="testadmin").first()
        assert admin_user is not None
        auth_service = AuthService(MongoUserRepository())
        auth_service.delete_user(user_id=str(admin_user.id))
    finally:
        user_deleted.disconnect(failing_listener)

    response = client.get("/api/admin/posts", headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error_code"] == "UNAUTHORIZED"
