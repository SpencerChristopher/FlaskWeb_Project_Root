import pytest
from src.models.user import User
from src.models.post import Post

@pytest.fixture
def author_user(app):
    user = User(username="testauthor", email="author@example.com", role="author")
    user.set_password("password")
    user.save()
    yield user
    user.delete()

@pytest.fixture
def author_headers(login_user_fixture, author_user):
    token = login_user_fixture("testauthor", "password")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def member_user(app):
    user = User(username="testmember", email="member@example.com", role="member")
    user.set_password("password")
    user.save()
    yield user
    user.delete()

@pytest.fixture
def member_headers(login_user_fixture, member_user):
    token = login_user_fixture("testmember", "password")
    return {"Authorization": f"Bearer {token}"}

def test_author_blocked_from_content_manage_routes(client, author_headers):
    """
    Regression Test: Prove that Author is currently blocked from routes 
    requiring content:manage (because we removed the temporary mapping).
    """
    response = client.get("/api/content/posts", headers=author_headers)
    # EXPECTED REGRESSION: 403 Forbidden
    assert response.status_code == 403

def test_member_blocked_from_content_manage_routes(client, member_headers):
    """
    Ensure Member is blocked from content management.
    """
    response = client.get("/api/content/posts", headers=member_headers)
    assert response.status_code == 403
