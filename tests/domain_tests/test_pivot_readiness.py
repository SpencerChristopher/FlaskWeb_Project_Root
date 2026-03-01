import pytest
from src.models.user import User
from src.models.post import Post
from src.events import post_deleted
from src.models.comment import Comment
from src.models.comment import Comment

class TestPivotReadiness:
    """
    Stage 4 Gate Tests: Verify domain integrity and pivot compatibility.
    These tests must pass BEFORE moving to Stage 5.
    """

    def test_gate_comment_model_exists(self):
        """
        Gate 4.1: The Comment model must be defined in src/models/comment.py.
        """
        assert Comment is not None, "Comment model has not been implemented in src/models/comment.py"

    def test_gate_referential_integrity_on_delete(self, app, signal_tracker):
        """
        Gate 4.2: Deleting a post MUST trigger a cleanup of its comments via signals.
        Verification of 'Service Layer Refactor' (Stage 3) and 'Domain Integrity' (Stage 4).
        """
        from src.services import get_post_service
        post_service = get_post_service()

        with app.app_context():
            # 1. Setup: Post with multiple comments
            author = User(username="pivot_author", email="pivot@test.com", role="admin")
            author.set_password("password")
            author.save()

            post = post_service.create_post(
                title="Integrity Test Post",
                content="Content",
                summary="Summary",
                is_published=True,
                author=author
            )
            post_id = str(post.id)

            # Create 3 comments
            for i in range(3):
                Comment(
                    content=f"Comment {i}",
                    author=author,
                    post=post
                ).save()

            assert Comment.objects(post=post_id).count() == 3

            # 2. Track Signal and Action
            from src.schemas import UserIdentity
            user_identity = UserIdentity(id=str(author.id), username=author.username, role=author.role, token_version=0)
            
            with signal_tracker(post_deleted) as tracker:
                post_service.delete_post(post_id, user=user_identity)
                assert tracker.called, "post_deleted signal was not emitted."

            # 3. Verification: Signal listener should have cleaned up comments
            # This check will fail until the listener is implemented in src/listeners.py
            remaining_comments = Comment.objects(post=post_id).count()
            assert remaining_comments == 0, f"Orphaned comments found: {remaining_comments}"

            # Cleanup user
            author.delete()

    def test_gate_api_backward_compatibility(self, client, setup_users):
        """
        Gate 4.3: Adding new domain models must not break existing API contracts.
        Ensures the modular monolith can scale without regressions.
        """
        # This test ensures basic GET /api/blog still works even with Comment model in place.
        response = client.get('/api/blog')
        assert response.status_code == 200
        assert 'posts' in response.json
        assert 'pagination' in response.json
