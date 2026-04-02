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

def test_author_can_access_content_manage_routes(client, author_headers):
    """
    Ensure Author can access content management routes (Stage 2 Fix).
    """
    response = client.get("/api/content/posts", headers=author_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_author_only_sees_own_posts(client, author_user, author_headers, admin_user):
    """
    Ensure Author only sees their own posts in the management list.
    """
    # 1. Author creates a post
    Post(title="Author Post", slug="author-post", content="content", author=author_user).save()
    # 2. Admin creates a post
    Post(title="Admin Post", slug="admin-post", content="content", author=admin_user).save()
    
    response = client.get("/api/content/posts", headers=author_headers)
    assert response.status_code == 200
    posts = response.json
    assert len(posts) == 1
    assert posts[0]["title"] == "Author Post"

def test_author_can_delete_own_post(client, author_user, author_headers):
    """
    Ensure Author can delete their own post.
    """
    post = Post(title="My Post", slug="my-post", content="content", author=author_user).save()
    post_id = str(post.id)
    
    response = client.delete(f"/api/content/posts/{post_id}", headers=author_headers)
    assert response.status_code == 200
    assert Post.objects(id=post_id).count() == 0

def test_admin_can_delete_others_post(client, author_user, admin_headers):
    """
    Ensure Admin can delete a post written by an Author (Admin Override).
    """
    post = Post(title="Author Post", slug="author-post-2", content="content", author=author_user).save()
    post_id = str(post.id)
    
    response = client.delete(f"/api/content/posts/{post_id}", headers=admin_headers)
    assert response.status_code == 200
    assert Post.objects(id=post_id).count() == 0

def test_member_blocked_from_content_manage_routes(client, member_headers):
    """
    Ensure Member is blocked from content management.
    """
    response = client.get("/api/content/posts", headers=member_headers)
    assert response.status_code == 403
