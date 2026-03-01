import os
import pytest


pytestmark = pytest.mark.risk

if os.environ.get("RUN_RISK_TESTS") != "1":
    pytest.skip("Risk tests are opt-in. Set RUN_RISK_TESTS=1 to run.", allow_module_level=True)


def test_risk_csp_header_present(client):
    resp = client.get("/")
    assert "Content-Security-Policy" in resp.headers, "CSP header missing."


def test_risk_hsts_header_present(client):
    resp = client.get("/")
    assert "Strict-Transport-Security" in resp.headers, "HSTS header missing."


def test_risk_referrer_policy_present(client):
    resp = client.get("/")
    assert "Referrer-Policy" in resp.headers, "Referrer-Policy header missing."


def test_risk_permissions_policy_present(client):
    resp = client.get("/")
    assert "Permissions-Policy" in resp.headers, "Permissions-Policy header missing."


def test_risk_cors_origins_configured():
    cors_origins = os.environ.get("CORS_ORIGINS", "").strip()
    assert cors_origins, "CORS_ORIGINS is empty; lock this down before SPA work."


def test_risk_rate_limit_storage_configured():
    storage_uri = os.environ.get("RATELIMIT_STORAGE_URI", "").strip()
    assert storage_uri, "RATELIMIT_STORAGE_URI not set; rate limiting not durable."


def test_risk_jwt_cookie_secure_enabled(app):
    assert app.config["JWT_COOKIE_SECURE"] is True, "JWT_COOKIE_SECURE should be true in prod."


def test_risk_jwt_csrf_enabled(app):
    assert app.config["JWT_COOKIE_CSRF_PROTECT"] is True, "JWT_COOKIE_CSRF_PROTECT should be true in prod."


def test_risk_access_token_ttl_short(app):
    ttl = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    assert ttl.total_seconds() <= 900, "Access token TTL should be <= 15 minutes."


def test_risk_refresh_token_ttl_reasonable(app):
    ttl = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    assert ttl.total_seconds() <= 604800, "Refresh token TTL should be <= 7 days."
