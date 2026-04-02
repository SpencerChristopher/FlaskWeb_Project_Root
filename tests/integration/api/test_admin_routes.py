import pytest
from src.models.user import User
from src.models.article import Article
from flask_jwt_extended import create_access_token
import datetime


@pytest.fixture
def test_admin_user(app):
    with app.app_context():
        admin_user = User(username="adminuser", email="admin@example.com", role="admin")
        admin_user.set_password("AdminPassword123")
        admin_user.save()
        yield admin_user
        admin_user.delete()


@pytest.fixture
def admin_headers(login_user_fixture, test_admin_user):
    token = login_user_fixture("adminuser", "AdminPassword123")
    return {"Authorization": f"Bearer {token}"}


class TestAdminArticleRoutes:
    """Tests for admin article management routes."""

    def test_get_article_with_invalid_id_format(self, client, admin_headers):
        invalid_id = "not-a-valid-objectid"
        response = client.get(
            f"/api/content/articles/{invalid_id}", headers=admin_headers
        )
        assert response.status_code == 400
        assert response.json["error_code"] == "BAD_REQUEST"

    def test_create_article_successful(self, client, admin_headers, test_admin_user):
        payload = {
            "title": "My New Test Article",
            "content": "This is the content of my new test article.",
            "summary": "Summary of my new test article.",
            "is_published": True,
        }
        # client.post is the HTTP method - DO NOT RENAME
        response = client.post(
            "/api/content/articles", headers=admin_headers, json=payload
        )
        assert response.status_code == 201
        assert "id" in response.json
        assert response.json["title"] == payload["title"]

    def test_get_article_successful(self, client, admin_headers, test_admin_user):
        with client.application.app_context():
            art = Article(
                title="Existing Article",
                slug="existing-article",
                content="Content.",
                summary="Summary.",
                author=test_admin_user,
                is_published=True,
            ).save()
            article_id = str(art.id)

        response = client.get(
            f"/api/content/articles/{article_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json["title"] == "Existing Article"

    def test_update_article_successful(self, client, admin_headers, test_admin_user):
        with client.application.app_context():
            art = Article(
                title="Article to Update",
                slug="article-to-update",
                content="Original.",
                summary="Original.",
                author=test_admin_user,
                is_published=False,
            ).save()
            article_id = str(art.id)

        updated_payload = {
            "title": "Updated Article Title",
            "content": "Updated content.",
            "summary": "Updated summary.",
            "is_published": True,
        }
        response = client.put(
            f"/api/content/articles/{article_id}",
            headers=admin_headers,
            json=updated_payload,
        )
        assert response.status_code == 200
        assert response.json["title"] == updated_payload["title"]

    def test_delete_article_successful(self, client, admin_headers, test_admin_user):
        with client.application.app_context():
            art = Article(
                title="Article to Delete",
                slug="article-to-delete",
                content="Content.",
                summary="Summary.",
                author=test_admin_user,
                is_published=True,
            ).save()
            article_id = str(art.id)

        response = client.delete(
            f"/api/content/articles/{article_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json["message"] == "Article deleted successfully"
