import pytest
from flask import g
from src.schemas import UserIdentity
from src.models.user import User

class TestIdentityResilience:
    """
    Guardrail tests for Stage 2: Lightweight User Identity.
    Ensures that token versioning is strictly enforced.
    """

    def test_token_version_mismatch_blocks_request(self, client, app, admin_user, admin_headers):
        """
        Gate 5.2.2: Changing the token_version in the DB must immediately invalidate 
        outstanding JWTs.
        """
        # 1. Verify access works initially
        resp = client.get("/api/content/posts", headers=admin_headers)
        assert resp.status_code == 200

        # 2. Increment token_version in DB
        with app.app_context():
            user = User.objects(id=admin_user.id).first()
            user.token_version += 1
            user.save()

        # 3. Next request with OLD token must fail
        resp = client.get("/api/content/posts", headers=admin_headers)
        
        assert resp.status_code == 401
        assert resp.get_json()["error_code"] == "UNAUTHORIZED"
        # The JWT loader in security.py catches this first and returns "revoked"
        assert "revoked" in resp.get_json()["message"].lower()
