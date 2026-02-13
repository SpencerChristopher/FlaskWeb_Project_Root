from datetime import datetime, timedelta

from flask_jwt_extended import create_access_token, decode_token

from src.models.token_blocklist import TokenBlocklist


class TestJWTAuthentication:
    """Tests for JWT authentication hardening."""

    def test_access_token_expiry(self, client, admin_user):
        with client.application.app_context():
            access_token = create_access_token(
                identity=str(admin_user.id),
                additional_claims={"roles": ["admin"], "tv": admin_user.token_version},
                expires_delta=timedelta(seconds=-1),
            )
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/admin/posts", headers=headers)
        assert response.status_code == 401

    def test_tampered_token_signature(self, client, admin_headers):
        tampered_token = admin_headers["Authorization"][7:] + "a"
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/api/admin/posts", headers=headers)
        assert response.status_code == 401
        data = response.json
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["message"] == "Signature verification failed or token is malformed."

    def test_blacklisted_token(self, client, admin_user, app):
        with app.app_context():
            access_token = create_access_token(
                identity=str(admin_user.id),
                additional_claims={"roles": ["admin"], "tv": admin_user.token_version},
            )
            decoded_token = decode_token(access_token)
            jti = decoded_token["jti"]
            expires = datetime.fromtimestamp(decoded_token["exp"])
            blocklisted_token = TokenBlocklist(jti=jti, expires_at=expires)
            blocklisted_token.save()

        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/admin/posts", headers=headers)
        assert response.status_code == 401
        data = response.json
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["message"] == "Token has been revoked."

    def test_admin_required_with_missing_roles_claim(self, client, app, regular_user):
        with app.app_context():
            access_token = create_access_token(
                identity=str(regular_user.id),
                additional_claims={"tv": regular_user.token_version},
            )
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/admin/posts", headers=headers)
        assert response.status_code == 403
        assert "Admin access required." in response.json["message"]

    def test_admin_required_with_non_list_roles_claim(self, client, app, regular_user):
        with app.app_context():
            access_token = create_access_token(
                identity=str(regular_user.id),
                additional_claims={"roles": "user", "tv": regular_user.token_version},
            )
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/admin/posts", headers=headers)
        assert response.status_code == 403
        assert "Admin access required." in response.json["message"]
