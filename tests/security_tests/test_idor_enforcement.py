import pytest
from src.models.user import User
from src.models.post import Post

def test_user_cannot_delete_others_post(client, setup_users, login_user_fixture):
    """
    Vulnerability Check (IDOR): Ensure a user with CONTENT_MANAGE but NOT the author
    cannot delete another person's post.
    """
    # 1. setup_users creates 'testadmin' (admin) and 'testuser' (member)
    admin_user, regular_user = setup_users
    
    # We need a second admin to test IDOR between users with same high-level permissions
    other_admin = User(username="otheradmin", email="other@example.com", role="admin")
    other_admin.set_password("password")
    other_admin.save()
    
    # 2. Admin A (Victim) creates a post
    post = Post(title="Victim Post", slug="victim-post", content="Secret data", author=admin_user)
    post.save()
    post_id = str(post.id)
    
    # 3. Admin B (Attacker) logs in
    # The fixture returns the access token
    attacker_token = login_user_fixture("otheradmin", "password")
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}
    
    # 4. Attacker attempts to delete Victim's post
    response = client.delete(f"/api/content/posts/{post_id}", headers=attacker_headers)
    
    # EXPECTATION: 401 Unauthorized (Ownership failure)
    assert response.status_code == 401
    assert Post.objects(id=post_id).count() == 1
