import pytest
from unittest.mock import patch
from src.models.article import Article


class TestErrorHandlingAndLogging:
    """
    Tests that the application handles errors gracefully.
    """

    def test_500_error_returns_json(self, client, admin_headers):
        """
        Verify that a 500 error returns a structured JSON response.
        """
        with patch("src.models.article.Article.objects") as mocked_objects:
            mocked_objects.side_effect = Exception("Simulating a database error")

            response = client.get("/api/content/articles", headers=admin_headers)

            assert response.status_code == 500
            data = response.get_json()
            assert data["error_code"] == "INTERNAL_SERVER_ERROR"

    def test_no_stack_trace_in_500_response(self, client, admin_headers):
        """
        Ensure that the 500 error response does not contain stack trace info.
        """
        with patch("src.models.article.Article.objects") as mocked_objects:
            mocked_objects.side_effect = Exception("Simulating a database error")

            response = client.get("/api/content/articles", headers=admin_headers)

            assert response.status_code == 500
            response_text = response.get_data(as_text=True)
            assert "Traceback" not in response_text
