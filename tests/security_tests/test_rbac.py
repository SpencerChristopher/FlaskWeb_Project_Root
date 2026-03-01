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
    """Tests for resource-centric permission control."""

    def test_admin_can_access_content_management(self, client, admin_headers):
        """Admins have content:manage permission."""
        response = client.get("/api/content/posts", headers=admin_headers)
        assert response.status_code == 200

    def test_author_can_access_content_management(self, client, content_admin_headers):
        """Authors have content:author permission (mapped to manage for now)."""
        response = client.get("/api/content/posts", headers=content_admin_headers)
        assert response.status_code == 200

    def test_member_cannot_access_management_route(self, client, user_headers):
        """Members have no management permissions."""
        response = client.get("/api/content/posts", headers=user_headers)
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"

    def test_member_cannot_create_post(self, client, user_headers):
        """Members cannot create content."""
        response = client.post(
            "/api/content/posts",
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

    def test_member_cannot_update_post(self, client, user_headers, admin_post):
        """Members cannot update content."""
        response = client.put(
            f"/api/content/posts/{admin_post}",
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

    def test_member_cannot_delete_post(self, client, user_headers, admin_post):
        """Members cannot delete content."""
        response = client.delete(f"/api/content/posts/{admin_post}", headers=user_headers)
        assert response.status_code == 403
        assert response.get_json()["error_code"] == "FORBIDDEN"
