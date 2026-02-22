import datetime

import pytest

from src.models.post import Post
from src.models.user import User


@pytest.fixture
def contract_user(app):
    user = User(username="contractuser", email="contract@example.com", role="user")
    user.set_password("Password123!")
    user.save()
    yield user
    user.delete()


@pytest.fixture
def contract_post(app, contract_user):
    post = Post(
        title="Contract Post Title",
        slug="contract-post-title",
        content="Contract post content",
        summary="Contract summary",
        author=contract_user,
        is_published=True,
        publication_date=datetime.datetime.now(datetime.UTC),
    )
    post.save()
    yield post
    post.delete()


@pytest.fixture
def admin_headers(setup_users, login_user_fixture):
    token = login_user_fixture("testadmin", "testpassword")
    return {"Authorization": f"Bearer {token}"}


def _assert_author_contract(author_payload):
    assert set(author_payload.keys()) == {"id", "username"}


def test_contract_blog_list_shape(client, contract_post):
    response = client.get("/api/blog")
    assert response.status_code == 200
    data = response.get_json()

    assert set(data.keys()) == {"posts", "pagination"}
    assert isinstance(data["posts"], list)
    assert isinstance(data["pagination"], dict)
    assert {
        "total_posts",
        "total_pages",
        "current_page",
        "per_page",
        "has_next",
        "has_prev",
    } <= set(data["pagination"].keys())

    assert len(data["posts"]) >= 1
    post_summary = next((p for p in data["posts"] if p["slug"] == contract_post.slug), None)
    assert post_summary is not None
    assert {"title", "summary", "slug", "publication_date"} <= set(post_summary.keys())


def test_contract_blog_detail_shape(client, contract_post):
    response = client.get(f"/api/blog/{contract_post.slug}")
    assert response.status_code == 200
    data = response.get_json()

    assert {
        "id",
        "title",
        "slug",
        "content",
        "summary",
        "author",
        "publication_date",
        "last_updated",
        "is_published",
    } <= set(data.keys())
    _assert_author_contract(data["author"])


def test_contract_auth_status_anonymous_shape(client):
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"logged_in": False}


def test_contract_login_shape_and_cookie_transport(client, setup_users):
    response = client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "testpassword"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"message": "Login successful"}
    assert "access_token" not in data
    assert "refresh_token" not in data

    cookies = response.headers.getlist("Set-Cookie")
    assert any("access_token_cookie=" in cookie for cookie in cookies)
    assert any("refresh_token_cookie=" in cookie for cookie in cookies)


def test_contract_admin_post_crud_shapes(client, admin_headers):
    create_payload = {
        "title": "Contract Admin Post",
        "slug": "contract-admin-post",
        "content": "Contract admin post content",
        "summary": "Contract admin summary",
        "is_published": True,
    }
    create_response = client.post("/api/admin/posts", headers=admin_headers, json=create_payload)
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert {
        "message",
        "id",
        "title",
        "slug",
        "content",
        "summary",
        "is_published",
        "author",
    } <= set(created.keys())
    _assert_author_contract(created["author"])

    post_id = created["id"]

    get_response = client.get(f"/api/admin/posts/{post_id}", headers=admin_headers)
    assert get_response.status_code == 200
    fetched = get_response.get_json()
    assert {
        "id",
        "title",
        "slug",
        "content",
        "summary",
        "author",
        "publication_date",
        "last_updated",
        "is_published",
    } <= set(fetched.keys())
    _assert_author_contract(fetched["author"])

    list_response = client.get("/api/admin/posts", headers=admin_headers)
    assert list_response.status_code == 200
    listed = list_response.get_json()
    assert isinstance(listed, list)
    assert any(item["id"] == post_id for item in listed)

    update_payload = {
        "title": "Contract Admin Post Updated",
        "slug": "contract-admin-post-updated",
        "content": "Updated content",
        "summary": "Updated summary",
        "is_published": False,
    }
    update_response = client.put(
        f"/api/admin/posts/{post_id}",
        headers=admin_headers,
        json=update_payload,
    )
    assert update_response.status_code == 200
    updated = update_response.get_json()
    assert {
        "message",
        "id",
        "title",
        "slug",
        "content",
        "summary",
        "is_published",
        "author",
    } <= set(updated.keys())
    _assert_author_contract(updated["author"])

    delete_response = client.delete(f"/api/admin/posts/{post_id}", headers=admin_headers)
    assert delete_response.status_code == 200
    assert delete_response.get_json() == {"message": "Post deleted successfully"}
