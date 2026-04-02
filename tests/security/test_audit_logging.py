import pytest
import logging
from unittest.mock import MagicMock, patch
from src.exceptions import ForbiddenException
from src.models.user import User


class TestAuditIntegrity:
    """
    Gating tests for Phase 5: Audit & Identity Optimization.
    Ensures security failures are logged and redundant DB calls are removed.
    """

    def test_unauthorized_access_is_logged_as_security_alert(
        self, client, user_headers, admin_article, caplog
    ):
        """
        Gate: Verify that a 403 Forbidden response generates a high-signal warning log.
        """
        article_id = str(admin_article.id)

        # 1. Trigger Forbidden (Member trying to delete Admin article)
        with caplog.at_level(logging.WARNING):
            resp = client.delete(
                f"/api/content/articles/{article_id}", headers=user_headers
            )

        assert resp.status_code == 403

        # 2. Verify Log Content
        assert "SECURITY ALERT" in caplog.text
        assert "unauthorized" in caplog.text.lower()
        # Should contain the path
        assert f"/api/content/articles/{article_id}" in caplog.text

    def test_article_creation_does_not_redundantly_hydrate_user(
        self, client, admin_headers, app
    ):
        """
        Gate: Article creation should trust the Identity DTO and NOT fetch the User model again.
        """

        # Define a side effect that actually performs the lookup to avoid breaking Auth.
        def real_get_by_id(user_id):
            return User.objects(id=user_id).first()

        # Patch the repository method but let it perform real work
        with patch(
            "src.repositories.mongo_user_repository.MongoUserRepository.get_by_id",
            side_effect=real_get_by_id,
        ) as mock_get_user:

            payload = {
                "title": f"Optimized Identity Test {datetime.datetime.now().timestamp()}",
                "content": "Content",
                "summary": "Summary",
                "is_published": False,
            }

            # 1. First call: Auth/Revocation check will call get_by_id
            resp = client.post(
                "/api/content/articles", json=payload, headers=admin_headers
            )
            assert resp.status_code == 201

            # 2. Analyze call count
            # Before optimization, this was 2:
            # - 1 for Auth/Revocation check
            # - 1 for ArticleService.create_article (author_model = ...)
            # After optimization, it should be exactly 1.
            assert (
                mock_get_user.call_count == 1
            ), f"Redundant User hydration detected! get_by_id called {mock_get_user.call_count} times. Expected 1 (Auth check only)."


import datetime
