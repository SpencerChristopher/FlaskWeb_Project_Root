import pytest
import requests
import os
import urllib3

# Suppress insecure request warnings for self-signed certs in staging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# These tests are intended to run against a LIVE production/staging instance.
# They verify that the 'Double Gate' and core infrastructure are operational.

class TestProdReadiness:
    """Smoke tests for production environments."""

    def test_api_bootstrap_public(self, prod_base_url):
        """Verify that bootstrap endpoint is reachable and returns public data."""
        url = f"{prod_base_url}/api/bootstrap"
        # We use verify=False for self-signed certs in staging/WSL
        resp = requests.get(url, verify=False)
        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert "auth" in data
        # Corrected key from 'authenticated' to 'logged_in'
        assert data["auth"]["logged_in"] is False

    def test_db_connectivity_via_blog_api(self, prod_base_url):
        """Verify that the blog API can fetch posts (DB Check)."""
        url = f"{prod_base_url}/api/blog"
        resp = requests.get(url, verify=False)
        assert resp.status_code == 200
        data = resp.json()
        # Corrected key from 'articles' to 'posts'
        assert "posts" in data
        assert isinstance(data["posts"], list)

    def test_unauthorized_content_access_blocked(self, prod_base_url):
        """Verify that administrative endpoints are correctly gated."""
        url = f"{prod_base_url}/api/content/articles"
        resp = requests.get(url, verify=False)
        # Should be 401 (Unauthorized) not 404 or 500
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "UNAUTHORIZED"

    def test_static_assets_available(self, prod_base_url):
        """Verify that Nginx is correctly serving static files."""
        # Check app.js (the core of our SPA)
        url = f"{prod_base_url}/static/app.js"
        resp = requests.get(url, verify=False)
        assert resp.status_code == 200
        assert "application/javascript" in resp.headers.get("Content-Type", "")
