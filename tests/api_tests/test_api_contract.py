import datetime
import pytest
from src.models.article import Article
from src.models.user import User


@pytest.fixture
def contract_user(app):
    user = User(username="contractuser", email="contract@example.com", role="member")
    user.set_password("Password123!")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def contract_article(app, contract_user):
    art = Article(
        title="Contract Article Title",
        slug="contract-article-title",
        content="Contract Article content",
        summary="Contract summary",
        author=contract_user,
        is_published=True,
        publication_date=datetime.datetime.now(datetime.timezone.utc),
    ).save()
    yield art
    art.delete()


@pytest.fixture
def admin_headers(setup_users, login_user_fixture):
    token = login_user_fixture("testadmin", "testpassword")
    return {"Authorization": f"Bearer {token}"}


def _assert_error_contract(data, expect_details=False):
    assert "error_code" in data
    assert "message" in data
    if expect_details:
        assert "details" in data
        assert isinstance(data["details"], list)


def test_contract_error_shape_on_404(client):
    response = client.get("/api/non-existent-route")
    assert response.status_code == 404
    data = response.get_json()
    _assert_error_contract(data)


def test_contract_blog_list_shape(client, contract_article):
    response = client.get("/api/blog")
    assert response.status_code == 200
    data = response.get_json()
    assert set(data.keys()) == {"posts", "pagination"}
    assert isinstance(data["posts"], list)
    art_summary = next(
        (p for p in data["posts"] if p["slug"] == contract_article.slug), None
    )
    assert art_summary is not None
    assert {"title", "summary", "slug", "publication_date"} <= set(art_summary.keys())


def test_contract_blog_detail_shape(client, contract_article):
    response = client.get(f"/api/blog/{contract_article.slug}")
    assert response.status_code == 200
    data = response.get_json()
    assert set(data.keys()) == {
        "id",
        "title",
        "slug",
        "content",
        "summary",
        "is_published",
        "publication_date",
        "last_updated",
        "author_id",
        "author_username",
    }
    assert "author" not in data


def test_contract_admin_article_crud_shapes(client, admin_headers):
    create_payload = {
        "title": "Admin Art",
        "content": "Content",
        "summary": "Summ",
        "is_published": True,
    }
    create_response = client.post(
        "/api/content/articles", headers=admin_headers, json=create_payload
    )
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert set(created.keys()) == {
        "id",
        "title",
        "slug",
        "content",
        "summary",
        "is_published",
        "publication_date",
        "last_updated",
        "author_id",
        "author_username",
    }
    assert "author" not in created

    article_id = created["id"]
    get_response = client.get(
        f"/api/content/articles/{article_id}", headers=admin_headers
    )
    assert get_response.status_code == 200

    delete_response = client.delete(
        f"/api/content/articles/{article_id}", headers=admin_headers
    )
    assert delete_response.status_code == 200
