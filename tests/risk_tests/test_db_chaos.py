import pytest
from mongoengine.connection import get_db
from unittest.mock import patch
from pymongo.errors import ConnectionFailure

@pytest.mark.chaos
class TestDatabaseChaos:
    """
    Simulates infrastructure failures for MongoDB to ensure application resilience.
    Target: 503 Service Unavailable for critical failures.
    """

    def test_get_posts_during_db_outage(self, client):
        """
        G4.1: If MongoDB is unreachable, the API must return 503.
        """
        # We patch the collection's 'find' method to simulate a connection loss
        # This is a robust way to simulate chaos without stopping Docker.
        with patch('mongoengine.queryset.QuerySet._cursor') as mocked_cursor:
            mocked_cursor.side_effect = ConnectionFailure("Simulated MongoDB failure")
            
            resp = client.get("/api/blog")
            
            # Currently this likely returns 500 (Unhandled Exception)
            # Implementation goal is 503.
            assert resp.status_code == 503
            data = resp.get_json()
            assert data["error_code"] == "SERVICE_UNAVAILABLE"
            assert "database" in data["message"].lower() or "service" in data["message"].lower()

    def test_login_during_db_outage(self, client):
        """
        Verify login flow handles DB failure gracefully.
        """
        credentials = {"username": "admin", "password": "any"}
        
        with patch('src.models.user.User.objects') as mocked_user_query:
            mocked_user_query.side_effect = ConnectionFailure("Simulated DB failure")
            
            resp = client.post("/api/auth/login", json=credentials)
            
            assert resp.status_code == 503
            assert resp.get_json()["error_code"] == "SERVICE_UNAVAILABLE"
