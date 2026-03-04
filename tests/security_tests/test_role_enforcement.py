import pytest
from src.models.article import Article

def test_author_can_access_content_manage_routes(client, content_admin_headers):
    response = client.get("/api/content/articles", headers=content_admin_headers)
    assert response.status_code == 200

def test_author_only_sees_own_articles(client, content_admin_user, content_admin_headers, admin_user):
    with client.application.app_context():
        Article(title="Author Art", slug="author-art", content="c", author=content_admin_user, is_published=True).save()
        Article(title="Admin Art", slug="admin-art", content="c", author=admin_user, is_published=True).save()

    response = client.get("/api/content/articles", headers=content_admin_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == "Author Art"

def test_author_can_delete_own_article(client, content_admin_user, content_admin_headers):
    with client.application.app_context():
        art = Article(title="My Art", slug="my-art", content="c", author=content_admin_user).save()
        article_id = str(art.id)

    response = client.delete(f"/api/content/articles/{article_id}", headers=content_admin_headers)
    assert response.status_code == 200

def test_admin_can_delete_others_article(client, content_admin_user, admin_headers):
    with client.application.app_context():
        art = Article(title="Author Art", slug="author-art-2", content="c", author=content_admin_user).save()
        article_id = str(art.id)

    response = client.delete(f"/api/content/articles/{article_id}", headers=admin_headers)
    assert response.status_code == 200
