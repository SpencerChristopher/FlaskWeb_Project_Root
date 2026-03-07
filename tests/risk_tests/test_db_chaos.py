import pytest
from unittest.mock import patch
from pymongo.errors import ConnectionFailure

@pytest.mark.chaos
class TestDatabaseChaos:
    """
    Simulates infrastructure failures for MongoDB to ensure application resilience.
    Target: 503 Service Unavailable for critical failures.
    """

    def test_get_Articles_during_db_outage(self, client):
        """
        G4.1: If MongoDB is unreachable during a blog listing, the API must return 503.
        """
        # Patch Article.objects (the attribute) to return a mock that simulates the QuerySet chain.
        with patch('src.models.article.Article.objects') as mocked_queryset:
            # The repository calls: Article.objects(is_published=True).only(...).order_by(...).paginate(...)
            # So Article.objects (the mock) when called returns another mock (the chain).
            mock_chain = mocked_queryset.return_value
            mock_chain.only.return_value.order_by.return_value.paginate.side_effect = ConnectionFailure("Simulated MongoDB failure")

            resp = client.get("/api/blog")

            assert resp.status_code == 503
            data = resp.get_json()
            assert data["error_code"] == "SERVICE_UNAVAILABLE"
            assert "database" in data["message"].lower() or "service" in data["message"].lower()

    def test_login_during_db_outage(self, client):
        """
        G4.1: If MongoDB is unreachable during login, the API must return 503.
        """
        credentials = {"username": "admin", "password": "any"}
        
        with patch('src.models.user.User.objects') as mocked_user_query:
            mocked_user_query.side_effect = ConnectionFailure("Simulated DB failure")
            
            resp = client.post("/api/auth/login", json=credentials)
            
            assert resp.status_code == 503
            data = resp.get_json()
            assert data["error_code"] == "SERVICE_UNAVAILABLE"
