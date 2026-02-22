import pytest

from src.exceptions import UnauthorizedException
from src.models.user import User
from src.repositories.mongo_user_repository import MongoUserRepository
from src.services.auth_service import AuthService


def test_auth_service_authenticate_success(app):
    auth_service = AuthService(MongoUserRepository())

    with app.app_context():
        user = User(username="auth_user", email="auth_user@example.com", role="user")
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
            role="user",
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
            role="user",
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
            role="user",
        )
        user.set_password("OldPassword123!")
        user.save()

        with pytest.raises(UnauthorizedException):
            auth_service.change_password(
                user_id=str(user.id),
                current_password="WrongCurrent123!",
                new_password="NewPassword456!",
            )
