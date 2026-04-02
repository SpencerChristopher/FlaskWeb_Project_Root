import pytest
from src.models.user import User
from src.models.article import Article
from src.models.comment import Comment
from src.repositories import get_comment_repository

@pytest.fixture
def test_data(app):
    with app.app_context():
        # Create author
        author = User(username="cleanupauthor", email="cleanup@example.com", role="member")
        author.set_password("testpassword")
        author.save()
        
        # Create another user for article author
        admin = User(username="cleanupadmin", email="admin-cleanup@example.com", role="admin")
        admin.set_password("testpassword")
        admin.save()
        
        # Create article
        article = Article(
            title="Cleanup Article", 
            slug="cleanup-article", 
            content="Content", 
            summary="Summary", 
            author=admin
        ).save()
        
        # Create comments by our target author
        comment_repo = get_comment_repository()
        comment1 = Comment(content="Comment 1", author=author, article=article).save()
        comment2 = Comment(content="Comment 2", author=author, article=article).save()
        
        yield {
            "author": author,
            "admin": admin,
            "article": article,
            "comments": [comment1, comment2]
        }
        
        # Cleanup if test fails
        Comment.objects(article=article).delete()
        article.delete()
        author.delete()
        admin.delete()

def test_user_deletion_cascades_comment_cleanup(app, test_data, login_user_fixture, client):
    author = test_data["author"]
    
    # Verify comments exist before deletion
    assert Comment.objects(author=author).count() == 2
    
    # Delete the user account via the API (which triggers the event)
    access_token = login_user_fixture(author.username, "testpassword")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Client handles its own context
    response = client.post(
        "/api/auth/delete-account", 
        json={"current_password": "testpassword"}, 
        headers=headers
    )
    assert response.status_code == 200
    
    # Need app context for DB checks
    with app.app_context():
        # Verify user is gone
        assert User.objects(id=author.id).first() is None
        
        # CRITICAL: Verify comments are cleaned up by the listener
        assert Comment.objects(author=author).count() == 0
