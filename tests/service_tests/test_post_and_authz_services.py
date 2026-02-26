import pytest

from src.events import post_created
from src.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from src.models.user import User
from src.services import get_authz_service, get_post_service


def test_authz_service_get_authenticated_user_success(app):
    authz_service = get_authz_service()

    with app.app_context():
        user = User(username="authz_user", email="authz_user@example.com", role="member")
        user.set_password("Password123!")
        user.save()

        resolved_user = authz_service.get_authenticated_user(str(user.id))
        assert resolved_user is not None
        assert resolved_user.username == "authz_user"


def test_authz_service_get_authenticated_user_missing_raises(app):
    authz_service = get_authz_service()

    with app.app_context():
        with pytest.raises(UnauthorizedException):
            authz_service.get_authenticated_user("65f0b4b4b4b4b4b4b4b4b4b4")


def test_authz_service_require_admin_role_check(app):
    authz_service = get_authz_service()

    with app.app_context():
        regular_user = User(
            username="non_admin",
            email="non_admin@example.com",
            role="member",
        )
        regular_user.set_password("Password123!")
        regular_user.save()

        with pytest.raises(ForbiddenException):
            authz_service.require_admin(str(regular_user.id), {"roles": ["member"], "tv": 0})


def test_authz_service_require_admin_allows_content_admin(app):
    authz_service = get_authz_service()

    with app.app_context():
        content_admin = User(
            username="content_admin_user",
            email="content_admin_user@example.com",
            role="author",
        )
        content_admin.set_password("Password123!")
        content_admin.save()

        resolved = authz_service.require_admin(
            str(content_admin.id),
            {"roles": ["author"], "tv": 0},
        )
        assert str(resolved.id) == str(content_admin.id)


def test_authz_service_require_admin_rejects_ops_admin(app):
    authz_service = get_authz_service()

    with app.app_context():
        ops_admin = User(
            username="ops_admin_user",
            email="ops_admin_user@example.com",
            role="member",
        )
        ops_admin.set_password("Password123!")
        ops_admin.save()

        with pytest.raises(ForbiddenException):
            authz_service.require_admin(
                str(ops_admin.id),
                {"roles": ["member"], "tv": 0},
            )


def test_authz_service_require_admin_accepts_legacy_admin_claims(app):
    authz_service = get_authz_service()

    with app.app_context():
        admin_user = User(
            username="legacy_admin_user",
            email="legacy_admin_user@example.com",
            role="admin",
        )
        admin_user.set_password("Password123!")
        admin_user.save()

        resolved = authz_service.require_admin(str(admin_user.id), {"roles": ["admin"], "tv": 0})
        assert str(resolved.id) == str(admin_user.id)

def test_post_service_create_update_conflict_path(app):
    post_service = get_post_service()

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
    post_service = get_post_service()

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


def test_post_service_create_emits_single_event_with_metadata(app):
    post_service = get_post_service()
    received_events = []

    def receiver(sender, **kwargs):
        received_events.append(kwargs)

    post_created.connect(receiver)
    try:
        with app.app_context():
            author = User(
                username="svc_emit_author",
                email="svc_emit_author@example.com",
                role="admin",
            )
            author.set_password("Password123!")
            author.save()

            created = post_service.create_post(
                title="Service Event Post",
                content="Service event content",
                summary="Service event summary",
                is_published=True,
                author=author,
            )

            assert created is not None
            assert len(received_events) == 1
            assert received_events[0]["event_type"] == "post-created"
            assert received_events[0]["post_id"] == str(created.id)
            assert "event_id" in received_events[0]
            assert "occurred_at" in received_events[0]
    finally:
        post_created.disconnect(receiver)
