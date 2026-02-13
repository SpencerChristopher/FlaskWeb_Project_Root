import pytest
from flask_jwt_extended import create_access_token

from src.models.user import User


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
def admin_headers(app, admin_user):
    """Return headers for an admin user."""
    access_token = create_access_token(
        identity=str(admin_user.id),
        additional_claims={"roles": ["admin"], "tv": admin_user.token_version},
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def user_headers(app, regular_user):
    """Return headers for a regular user."""
    access_token = create_access_token(
        identity=str(regular_user.id),
        additional_claims={"roles": ["user"], "tv": regular_user.token_version},
    )
    return {"Authorization": f"Bearer {access_token}"}
