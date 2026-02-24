import pytest
from src.events import user_role_changed, post_published
from src.services.auth_service import AuthService
from src.repositories.mongo_user_repository import MongoUserRepository
from src.repositories.mongo_post_repository import MongoPostRepository
from src.services.post_service import PostService
from src.models.user import User
from src.models.post import Post

class TestEventSystem:
    """
    Integration tests for the Blinker event system.
    These tests verify that critical business logic correctly emits signals.
    """

    def test_user_role_change_emits_signal(self, app, signal_tracker):
        """
        Verify that AuthService.change_role correctly emits the user_role_changed signal.
        """
        from src.services import get_auth_service
        auth_service = get_auth_service()

        with app.app_context():
            # 1. Setup: Create a test user
            user = User(username="event_test_user", email="event@test.com", role="member")
            user.set_password("Password123!")
            user.save()
            user_id = str(user.id)

            # 2. Track Signal: Connect the tracker to user_role_changed
            with signal_tracker(user_role_changed) as tracker:
                # 3. Action: Change the user's role
                auth_service.change_role(user_id=user_id, role="admin")

                # 4. Assert: Verify the signal was received with the correct payload
                assert tracker.called, "Signal 'user_role_changed' was not emitted."
                assert tracker.data["user_id"] == user_id
                assert tracker.data["new_role"] == "admin"
                assert tracker.data["event_type"] == "user-role-changed"

            # Cleanup
            user.delete()

    def test_post_published_emits_signal(self, app, signal_tracker):
        """
        Verify that PostService.update_post correctly emits the post_published signal
        when a post's status is changed to published.
        """
        from src.services import get_post_service
        post_service = get_post_service()

        with app.app_context():
            # 1. Setup: Create a draft post
            author = User(username="post_event_author", email="post_event@test.com", role="admin")
            author.set_password("Password123!")
            author.save()

            draft_post = post_service.create_post(
                title="Draft Post for Event",
                content="Content",
                summary="Summary",
                is_published=False,
                author=author
            )
            post_id = str(draft_post.id)

            # 2. Track Signal: Connect the tracker to post_published
            from src.events import post_published
            with signal_tracker(post_published) as tracker:
                # 3. Action: Update the post to be published
                post_service.update_post(
                    post_id=post_id,
                    title=draft_post.title,
                    content=draft_post.content,
                    summary=draft_post.summary,
                    is_published=True
                )

                # 4. Assert: Verify the signal was received with the correct payload
                assert tracker.called, "Signal 'post_published' was not emitted."
                assert tracker.data["post_id"] == post_id
                assert tracker.data["event_type"] == "post-published"
            
            # Cleanup
            post_service.delete_post(post_id)
            author.delete()
