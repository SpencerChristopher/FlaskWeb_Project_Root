import pytest
from src.events import user_role_changed
from src.services.auth_service import AuthService
from src.repositories.mongo_user_repository import MongoUserRepository
from src.models.user import User

class TestEventSystem:
    """
    Integration tests for the Blinker event system.
    These tests verify that critical business logic correctly emits signals.
    """

    def test_user_role_change_emits_signal(self, app, signal_tracker):
        """
        Verify that AuthService.change_role correctly emits the user_role_changed signal.
        """
        user_repository = MongoUserRepository()
        auth_service = AuthService(user_repository)

        with app.app_context():
            # 1. Setup: Create a test user
            user = User(username="event_test_user", email="event@test.com", role="user")
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
