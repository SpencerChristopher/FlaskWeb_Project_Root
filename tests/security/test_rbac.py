import pytest
from src.models.article import Article


@pytest.fixture
def admin_article(app, admin_user):
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


class TestRBAC:
    def test_admin_can_access_content_management(self, client, admin_headers):
        response = client.get("/api/content/articles", headers=admin_headers)
        assert response.status_code == 200

    def test_member_cannot_access_management_route(self, client, user_headers):
        response = client.get("/api/content/articles", headers=user_headers)
        assert response.status_code == 403

    def test_member_cannot_create_article(self, client, user_headers):
        response = client.post(
            "/api/content/articles",
            headers=user_headers,
            json={
                "title": "No",
                "content": "No",
                "summary": "No",
                "is_published": False,
            },
        )
        assert response.status_code == 403

    def test_member_cannot_update_article(self, client, user_headers, admin_article):
        article_id = str(admin_article.id)
        response = client.put(
            f"/api/content/articles/{article_id}",
            headers=user_headers,
            json={"title": "Hack"},
        )
        assert response.status_code == 403
