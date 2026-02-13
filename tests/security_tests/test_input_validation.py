class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_create_post_invalid_payload(self, client, admin_headers):
        payload = {"title": "Invalid Post"}
        response = client.post("/api/admin/posts", headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json["error_code"] == "BAD_REQUEST"
        assert response.json["message"] == "Invalid post data"
        assert isinstance(response.json["details"], list)
        assert any(
            err["loc"] == ["summary"] and err["msg"] == "Field required"
            for err in response.json["details"]
        )
        assert any(
            err["loc"] == ["content"] and err["msg"] == "Field required"
            for err in response.json["details"]
        )

    def test_create_post_oversized_title(self, client, admin_headers):
        payload = {
            "title": "a" * 201,
            "content": "This is the content.",
            "summary": "This is the summary.",
        }
        response = client.post("/api/admin/posts", headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json["error_code"] == "BAD_REQUEST"
        assert response.json["message"] == "Invalid post data"
        assert isinstance(response.json["details"], list)
        assert any(
            err["loc"] == ["title"] and "at most 200 characters" in err["msg"]
            for err in response.json["details"]
        )

    def test_create_post_xss_payload(self, client, admin_headers):
        payload = {
            "title": "XSS Test",
            "content": '<script>alert("xss")</script>',
            "summary": "This is a summary.",
        }
        response = client.post("/api/admin/posts", headers=admin_headers, json=payload)
        assert response.status_code == 201
        assert response.json["content"] == '&lt;script&gt;alert("xss")&lt;/script&gt;'
