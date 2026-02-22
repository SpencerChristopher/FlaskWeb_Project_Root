import pytest
from flask_jwt_extended import create_access_token

from src.models.user import User
from src.repositories.mongo_user_repository import MongoUserRepository
from src.services.auth_service import AuthService


@pytest.fixture
def admin_user(client):
    """Create and return an admin user."""
    user = User(username="testadmin", email="admin@test.com", role="admin")
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def regular_user(client):
    """Create and return a regular user."""
    user = User(username="testuser", email="user@test.com", role="user")
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def content_admin_user(client):
    """Create and return a content admin user."""
    user = User(
        username="contentadmin",
        email="contentadmin@test.com",
        role="content_admin",
    )
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def ops_admin_user(client):
    """Create and return an ops admin user."""
    user = User(username="opsadmin", email="opsadmin@test.com", role="ops_admin")
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def admin_headers(app, admin_user):
    """Return headers for an admin user."""
    auth_service = AuthService(MongoUserRepository())
    access_token = create_access_token(
        identity=str(admin_user.id),
        additional_claims=auth_service.build_token_claims(admin_user),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def user_headers(app, regular_user):
    """Return headers for a regular user."""
    auth_service = AuthService(MongoUserRepository())
    access_token = create_access_token(
        identity=str(regular_user.id),
        additional_claims=auth_service.build_token_claims(regular_user),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def content_admin_headers(app, content_admin_user):
    """Return headers for a content admin user."""
    auth_service = AuthService(MongoUserRepository())
    access_token = create_access_token(
        identity=str(content_admin_user.id),
        additional_claims=auth_service.build_token_claims(content_admin_user),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def ops_admin_headers(app, ops_admin_user):
    """Return headers for an ops admin user."""
    auth_service = AuthService(MongoUserRepository())
    access_token = create_access_token(
        identity=str(ops_admin_user.id),
        additional_claims=auth_service.build_token_claims(ops_admin_user),
    )
    return {"Authorization": f"Bearer {access_token}"}
