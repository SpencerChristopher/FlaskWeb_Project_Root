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
    """Create and return a regular user (Member)."""
    user = User(username="testuser", email="user@test.com", role="member")
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def content_admin_user(client):
    """Create and return a content-focused user (Author)."""
    user = User(
        username="contentauthor",
        email="author@test.com",
        role="author",
    )
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def ops_admin_user(client):
    """Create and return a user who used to be ops admin (now Member)."""
    user = User(username="opsuser", email="opsuser@test.com", role="member")
    user.set_password("password")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def admin_headers(app, admin_user):
    """Return headers for an admin user."""
    from src.services import get_auth_service

    auth_service = get_auth_service()
    access_token = create_access_token(
        identity=str(admin_user.id),
        additional_claims=auth_service.build_token_claims(admin_user),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def user_headers(app, regular_user):
    """Return headers for a regular user."""
    from src.services import get_auth_service

    auth_service = get_auth_service()
    access_token = create_access_token(
        identity=str(regular_user.id),
        additional_claims=auth_service.build_token_claims(regular_user),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def content_admin_headers(app, content_admin_user):
    """Return headers for a content user (Author)."""
    from src.services import get_auth_service

    auth_service = get_auth_service()
    access_token = create_access_token(
        identity=str(content_admin_user.id),
        additional_claims=auth_service.build_token_claims(content_admin_user),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_article(app, admin_user):
    from src.models.article import Article

    with app.app_context():
        art = Article(
            title="Admin Draft",
            slug="admin-draft",
            content="Content.",
            summary="Summary.",
            author=admin_user,
            is_published=False,
        ).save()
        yield art
        art.delete()
