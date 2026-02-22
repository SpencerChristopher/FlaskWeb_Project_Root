import pytest

from src.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from src.models.user import User
from src.repositories.mongo_post_repository import MongoPostRepository
from src.repositories.mongo_user_repository import MongoUserRepository
from src.services.authz_service import AuthzService
from src.services.post_service import PostService


def test_authz_service_get_authenticated_user_success(app):
    user_repository = MongoUserRepository()
    authz_service = AuthzService(user_repository)

    with app.app_context():
        user = User(username="authz_user", email="authz_user@example.com", role="user")
        user.set_password("Password123!")
        user.save()

        resolved_user = authz_service.get_authenticated_user(str(user.id))
        assert resolved_user is not None
        assert resolved_user.username == "authz_user"


def test_authz_service_get_authenticated_user_missing_raises(app):
    user_repository = MongoUserRepository()
    authz_service = AuthzService(user_repository)

    with app.app_context():
        with pytest.raises(UnauthorizedException):
            authz_service.get_authenticated_user("65f0b4b4b4b4b4b4b4b4b4b4")


def test_authz_service_require_admin_role_check(app):
    user_repository = MongoUserRepository()
    authz_service = AuthzService(user_repository)

    with app.app_context():
        regular_user = User(
            username="non_admin",
            email="non_admin@example.com",
            role="user",
        )
        regular_user.set_password("Password123!")
        regular_user.save()

        with pytest.raises(ForbiddenException):
            authz_service.require_admin(str(regular_user.id), {"roles": ["user"]})


def test_post_service_create_update_conflict_path(app):
    post_repository = MongoPostRepository()
    post_service = PostService(post_repository)

    with app.app_context():
        author = User(username="svc_admin", email="svc_admin@example.com", role="admin")
        author.set_password("Password123!")
        author.save()

        created = post_service.create_post(
            title="Service Layer Post",
            content="Service content",
            summary="Service summary",
            is_published=True,
            author=author,
        )
        assert created.slug == "service-layer-post"
        assert created.publication_date is not None

        with pytest.raises(ConflictException):
            post_service.create_post(
                title="Service Layer Post",
                content="Duplicate",
                summary="Duplicate",
                is_published=False,
                author=author,
            )


def test_post_service_list_published_filters_drafts(app):
    post_repository = MongoPostRepository()
    post_service = PostService(post_repository)

    with app.app_context():
        author = User(username="svc_writer", email="svc_writer@example.com", role="admin")
        author.set_password("Password123!")
        author.save()

        post_service.create_post(
            title="Published Via Service",
            content="Published content",
            summary="Published summary",
            is_published=True,
            author=author,
        )
        post_service.create_post(
            title="Draft Via Service",
            content="Draft content",
            summary="Draft summary",
            is_published=False,
            author=author,
        )

        paginated = post_service.list_published_posts(page=1, per_page=10)
        assert paginated.total == 1
        assert paginated.items[0].slug == "published-via-service"
