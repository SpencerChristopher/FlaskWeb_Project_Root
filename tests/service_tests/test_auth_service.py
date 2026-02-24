import pytest

from src.events import user_deleted
from src.exceptions import UnauthorizedException
from src.models.user import User
from src.repositories.mongo_user_repository import MongoUserRepository
from src.services.auth_service import AuthService


def test_auth_service_authenticate_success(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(username="auth_user", email="auth_user@example.com", role="member")
        user.set_password("Password123!")
        user.save()

        authenticated_user = auth_service.authenticate("auth_user", "Password123!")
        assert authenticated_user.id == user.id


def test_auth_service_authenticate_invalid_password_raises(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_invalid",
            email="auth_invalid@example.com",
            role="member",
        )
        user.set_password("Password123!")
        user.save()

        with pytest.raises(UnauthorizedException):
            auth_service.authenticate("auth_invalid", "wrong-password")


def test_auth_service_change_password_success(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_change_pw",
            email="auth_change_pw@example.com",
            role="member",
        )
        user.set_password("OldPassword123!")
        user.save()

        auth_service.change_password(
            user_id=str(user.id),
            current_password="OldPassword123!",
            new_password="NewPassword456!",
        )

        refreshed_user = User.objects(id=user.id).first()
        assert refreshed_user is not None
        assert refreshed_user.check_password("NewPassword456!")


def test_auth_service_change_password_invalid_current_raises(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_bad_current",
            email="auth_bad_current@example.com",
            role="member",
        )
        user.set_password("OldPassword123!")
        user.save()

        with pytest.raises(UnauthorizedException):
            auth_service.change_password(
                user_id=str(user.id),
                current_password="WrongCurrent123!",
                new_password="NewPassword456!",
            )


def test_auth_service_change_role_increments_token_version(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_role_change",
            email="auth_role_change@example.com",
            role="member",
        )
        user.set_password("Password123!")
        user.save()
        initial_token_version = user.token_version

        updated_user = auth_service.change_role(user_id=str(user.id), role="author")
        assert updated_user.role == "author"
        assert updated_user.token_version == initial_token_version + 1


def test_auth_service_change_role_same_value_no_version_bump(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_role_same",
            email="auth_role_same@example.com",
            role="member",
        )
        user.set_password("Password123!")
        user.save()
        initial_token_version = user.token_version

        updated_user = auth_service.change_role(user_id=str(user.id), role="member")
        assert updated_user.role == "member"
        assert updated_user.token_version == initial_token_version


def test_auth_service_build_token_claims_admin_transition_mapping(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_claims_admin",
            email="auth_claims_admin@example.com",
            role="admin",
        )
        user.set_password("Password123!")
        user.save()

        claims = auth_service.build_token_claims(user)
        assert claims["tv"] == user.token_version
        assert claims["roles"] == ["admin"]
        assert "capabilities" not in claims


def test_auth_service_build_token_claims_content_admin_scope(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_claims_content_admin",
            email="auth_claims_content_admin@example.com",
            role="author",
        )
        user.set_password("Password123!")
        user.save()

        claims = auth_service.build_token_claims(user)
        assert claims["roles"] == ["author"]
        assert "capabilities" not in claims


def test_auth_service_delete_user_removes_record(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(
            username="auth_delete_user",
            email="auth_delete_user@example.com",
            role="member",
        )
        user.set_password("Password123!")
        user.save()
        user_id = str(user.id)

        auth_service.delete_user(user_id=user_id)
        assert User.objects(id=user_id).first() is None


def test_auth_service_delete_user_emits_signal(app):
    auth_service = AuthService(MongoUserRepository())
    received_events = []

    def receiver(sender, **kwargs):
        received_events.append(kwargs)

    user_deleted.connect(receiver)
    try:
        with app.app_context():
            user = User(
                username="auth_delete_signal",
                email="auth_delete_signal@example.com",
                role="member",
            )
            user.set_password("Password123!")
            user.save()
            user_id = str(user.id)

            auth_service.delete_user(user_id=user_id)
            assert len(received_events) == 1
            assert received_events[0]["user_id"] == user_id
            assert received_events[0]["event_type"] == "user-deleted"
            assert "event_id" in received_events[0]
            assert "occurred_at" in received_events[0]
    finally:
        user_deleted.disconnect(receiver)
