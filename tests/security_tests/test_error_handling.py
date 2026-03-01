from src.models.post import Post


class TestErrorHandlingAndLogging:
    """Tests for error handling and logging behavior."""

    def test_500_error_returns_json(self, client, admin_headers, monkeypatch):
        def mock_objects(*args, **kwargs):
            raise Exception("Simulating a database error")

        monkeypatch.setattr(Post, "objects", mock_objects)

        response = client.get("/api/content/posts", headers=admin_headers)
        assert response.status_code == 500
        assert response.headers["Content-Type"] == "application/json"
        assert response.json["error_code"] == "INTERNAL_SERVER_ERROR"
        assert response.json["message"] == "An unexpected error occurred."

    def test_no_stack_trace_in_500_response(self, client, admin_headers, monkeypatch):
        def mock_objects(*args, **kwargs):
            raise Exception("Simulating a database error")

        monkeypatch.setattr(Post, "objects", mock_objects)

        response = client.get("/api/content/posts", headers=admin_headers)
        assert response.status_code == 500
        assert b"Traceback" not in response.data
