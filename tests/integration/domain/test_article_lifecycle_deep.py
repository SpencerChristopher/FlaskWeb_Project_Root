import pytest
import os
from src.models.user import User
from src.models.article import Article
from src.events import article_created, article_deleted
from src.schemas import ArticlePublic

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

@pytest.mark.integration
class TestArticleLifecycleDeep:
    """
    Deep Integration Test for the Article Lifecycle.
    
    Path Traced:
    Route (content_management_routes.POST) 
    -> Schema (ArticleCreateUpdate Validation & Sanitization)
    -> Service (Slug generation & Timestamping)
    -> Repository (MongoEngine Save)
    -> Database (MongoDB 'posts' collection state)
    -> Signal (Blinker Event Dispatch)
    """

    def test_article_full_lifecycle_and_state(self, client, admin_headers, signal_tracker, app):
        # 1. SETUP: Prepare Payload with HTML to verify sanitization
        payload = {
            "title": "Deep Integration Test Article",
            "content": "<p>Content with <b>bold</b> and <script>alert('xss')</script></p>",
            "summary": "Summary with <i>italic</i>",
            "is_published": True
        }

        # 2. EXECUTE & SIGNAL CHECK: Create via API
        with signal_tracker(article_created) as tracker:
            response = client.post(
                "/api/content/articles", 
                headers=admin_headers, 
                json=payload
            )
            
            # Assert Transport Success
            assert response.status_code == 201
            data = response.json
            article_id = data["id"]
            
            # Assert Signal Emission
            assert tracker.called
            assert tracker.data["article_id"] == article_id

        # 3. SCHEMA VALIDATION: Verify DTO Integrity
        # This ensures the API response strictly matches the public contract
        ArticlePublic(**data)
        
        # 4. DEEP STATE VERIFICATION: Query MongoDB directly
        with app.app_context():
            db_article = Article.objects(id=article_id).first()
            assert db_article is not None
            assert db_article.title == payload["title"]
            assert db_article.slug == "deep-integration-test-article"
            
            # Verify Sanitization (DTO -> Service -> Repo -> DB)
            # <script> should be removed, <b> should persist
            assert "<script>" not in db_article.content
            assert "<b>" in db_article.content
            # Summary should have all tags stripped
            assert "<i>" not in db_article.summary

        # 5. DELETE & CLEANUP VERIFICATION
        with signal_tracker(article_deleted) as del_tracker:
            del_response = client.delete(
                f"/api/content/articles/{article_id}", 
                headers=admin_headers
            )
            assert del_response.status_code == 200
            assert del_tracker.called

        # 6. FINAL DEEP STATE VERIFICATION: Ensure hard deletion
        with app.app_context():
            assert Article.objects(id=article_id).first() is None

    def test_article_slug_conflict_prevents_db_write(self, client, admin_headers, app):
        """Verify that a conflict (409) prevents any state change in MongoDB."""
        payload = {
            "title": "Duplicate Title",
            "content": "Original Content",
            "summary": "Summary",
            "is_published": True
        }

        # Create the first one
        client.post("/api/content/articles", headers=admin_headers, json=payload)
        
        with app.app_context():
            initial_count = Article.objects(title=payload["title"]).count()
            assert initial_count == 1

        # Attempt to create the second one with same title
        response = client.post("/api/content/articles", headers=admin_headers, json=payload)
        assert response.status_code == 409
        
        # DEEP CHECK: Ensure no second document was created
        with app.app_context():
            final_count = Article.objects(title=payload["title"]).count()
            assert final_count == 1
