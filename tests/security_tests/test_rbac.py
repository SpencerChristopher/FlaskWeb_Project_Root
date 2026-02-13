class TestRBAC:
    """Tests for role-based access control."""

    def test_admin_can_access_admin_route(self, client, admin_headers):
        response = client.get("/api/admin/posts", headers=admin_headers)
        assert response.status_code == 200

    def test_user_cannot_access_admin_route(self, client, user_headers):
        response = client.get("/api/admin/posts", headers=user_headers)
        assert response.status_code == 403
