import pytest
import os

@pytest.mark.integration
class TestHttpsRedirectionDeep:
    """
    Deep Integration Test for HTTPS enforcement.
    Verifies that Talisman correctly interprets proxy headers.
    """

    def test_https_redirection_enforced_locally(self, monkeypatch):
        # 1. SETUP: Force HTTPS and clear session-scoped state
        monkeypatch.setenv("TALISMAN_FORCE_HTTPS", "true")
        
        # We manually create a fresh app and client to ensure it picks up the env
        from src.server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        
        # 2. EXECUTE: Request without HTTPS header
        response = client.get("/api/home")
        
        # If Talisman is working, it should return a 302/301 redirect to https://
        assert response.status_code in [301, 302]
        assert "https://" in response.headers["Location"]

    def test_https_proxy_header_bypasses_redirection(self, monkeypatch):
        # 1. SETUP: Force HTTPS
        monkeypatch.setenv("TALISMAN_FORCE_HTTPS", "true")
        
        from src.server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        
        # 2. EXECUTE: Request WITH X-Forwarded-Proto: https
        # This simulates a request that already passed through Nginx/Cloudflare
        response = client.get("/api/home", headers={"X-Forwarded-Proto": "https"})
        
        # Should return 200 OK (no redirect)
        assert response.status_code == 200
