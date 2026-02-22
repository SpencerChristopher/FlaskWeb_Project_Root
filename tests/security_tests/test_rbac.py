import datetime
import pytest

from src.models.post import Post


@pytest.fixture
def admin_post(app, admin_user):
    with app.app_context():
        post = Post(
            title="Admin Draft",
            slug="admin-draft",
            content="Admin only content.",
            summary="Admin summary.",
            author=admin_user,
            is_published=False,
            publication_date=datetime.datetime.now(datetime.UTC),
        )
        post.save()
        post_id = str(post.id)

    yield post_id

    with app.app_context():
        Post.objects(id=post_id).delete()


class TestRBAC:
    """Tests for role-based access control."""

    def test_admin_can_access_admin_route(self, client, admin_headers):
        response = client.get("/api/admin/posts", headers=admin_headers)
        assert response.status_code == 200

    def test_content_admin_can_access_admin_route(self, client, content_admin_headers):
        response = client.get("/api/admin/posts", headers=content_admin_headers)
        assert response.status_code == 200

    def test_ops_admin_cannot_access_content_admin_route(self, client, ops_admin_headers):
        response = client.get("/api/admin/posts", headers=ops_admin_headers)
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"

    def test_user_cannot_access_admin_route(self, client, user_headers):
        response = client.get("/api/admin/posts", headers=user_headers)
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"

    def test_user_cannot_create_admin_post(self, client, user_headers):
        response = client.post(
            "/api/admin/posts",
            headers=user_headers,
            json={
                "title": "No Access",
                "content": "Forbidden create attempt.",
                "summary": "Forbidden",
                "is_published": False,
            },
        )
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"

    def test_user_cannot_update_admin_post(self, client, user_headers, admin_post):
        response = client.put(
            f"/api/admin/posts/{admin_post}",
            headers=user_headers,
            json={
                "title": "No Access Update",
                "content": "Forbidden update attempt.",
                "summary": "Forbidden update",
                "is_published": False,
            },
        )
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"

    def test_user_cannot_delete_admin_post(self, client, user_headers, admin_post):
        response = client.delete(f"/api/admin/posts/{admin_post}", headers=user_headers)
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"
