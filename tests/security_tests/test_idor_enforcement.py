import pytest
from src.models.user import User
from src.models.article import Article


def test_user_cannot_delete_others_Article(client, setup_users, login_user_fixture):
    """
    Vulnerability Check (IDOR): Ensure a user with CONTENT_AUTHOR but NOT the author
    cannot delete another person's Article.
    """
    # 1. setup_users creates 'testadmin' (admin) and 'testuser' (member)
    admin_user, regular_user = setup_users

    # We need a second author to test IDOR between users with same restricted permissions
    other_author = User(
        username="otherauthor", email="otherauthor@example.com", role="author"
    )
    other_author.set_password("password")
    other_author.save()

    # 2. Admin A (Victim) creates a Article
    with client.application.app_context():
        art = Article(
            title="Victim Article",
            slug="victim-Article",
            content="Secret data",
            author=admin_user,
        )
        art.save()
        article_id = str(art.id)

    # 3. Author B (Attacker) logs in
    attacker_token = login_user_fixture("otherauthor", "password")
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}

    # 4. Attacker attempts to delete Victim's Article
    response = client.delete(
        f"/api/content/articles/{article_id}", headers=attacker_headers
    )

    # EXPECTATION: 403 Forbidden (Ownership failure)
    assert response.status_code == 403
    assert Article.objects(id=article_id).count() == 1
