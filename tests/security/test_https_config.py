"""
Tests for verifying HTTPS-related JWT cookie configurations.
These tests are designed to initially fail until the application
is properly configured to run over HTTPS and set secure cookies.
"""

import os
import pytest
from flask import Flask
import re


def test_jwt_cookie_secure_config(app: Flask):
    """
    Tests that JWT_COOKIE_SECURE is set to True when running in a secure context.
    This test will fail if the configuration is not set to True, which is expected
    for development HTTPS setup.
    """
    if os.environ.get("REQUIRE_HTTPS", "").lower() not in {"1", "true", "yes"}:
        pytest.skip("HTTPS-only check (set REQUIRE_HTTPS=1 to enforce).")
    assert app.config[
        "JWT_COOKIE_SECURE"
    ], "JWT_COOKIE_SECURE should be True for HTTPS environment."


def test_secure_flag_on_login_cookies(client, setup_users, app: Flask):
    """
    Tests that the access_token_cookie, refresh_token_cookie, and csrf_access_token
    are set with the 'Secure' flag after a successful login.
    This is a requirement when JWT_COOKIE_SECURE is True and the application is
    served over HTTPS.
    """
    if os.environ.get("REQUIRE_HTTPS", "").lower() not in {"1", "true", "yes"}:
        pytest.skip("HTTPS-only check (set REQUIRE_HTTPS=1 to enforce).")
    # We will directly manipulate app.config for this test session to ensure
    # JWT_COOKIE_CSRF_PROTECT is True and allows the csrf_access_token to be set.
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True

    res = client.post(
        "/api/auth/login", json={"username": "testadmin", "password": "testpassword"}
    )

    assert res.status_code == 200

    set_cookie_headers = res.headers.getlist("Set-Cookie")

    # Check for access_token_cookie with Secure flag
    access_cookie_found = False
    for cookie_header in set_cookie_headers:
        if "access_token_cookie" in cookie_header:
            access_cookie_found = True
            assert (
                "Secure" in cookie_header
            ), f"access_token_cookie missing 'Secure' flag: {cookie_header}"
            assert (
                "HttpOnly" in cookie_header
            ), f"access_token_cookie missing 'HttpOnly' flag: {cookie_header}"
            assert (
                "SameSite=Lax" in cookie_header
                or "SameSite=Strict" in cookie_header
                or "SameSite=None" in cookie_header
            ), f"access_token_cookie missing SameSite attribute: {cookie_header}"
            break
    assert access_cookie_found, "access_token_cookie not found in response headers"

    # Check for refresh_token_cookie with Secure flag
    refresh_cookie_found = False
    for cookie_header in set_cookie_headers:
        if "refresh_token_cookie" in cookie_header:
            refresh_cookie_found = True
            assert (
                "Secure" in cookie_header
            ), f"refresh_token_cookie missing 'Secure' flag: {cookie_header}"
            assert (
                "HttpOnly" in cookie_header
            ), f"refresh_token_cookie missing 'HttpOnly' flag: {cookie_header}"
            assert (
                "SameSite=Lax" in cookie_header
                or "SameSite=Strict" in cookie_header
                or "SameSite=None" in cookie_header
            ), f"refresh_token_cookie missing SameSite attribute: {cookie_header}"
            break
    assert refresh_cookie_found, "refresh_token_cookie not found in response headers"

    # Check for csrf_access_token with Secure flag (only if CSRF is enabled)
    csrf_cookie_found = False
    if app.config.get(
        "JWT_COOKIE_CSRF_PROTECT", False
    ):  # Check actual config, not manager's internal
        for cookie_header in set_cookie_headers:
            if "csrf_access_token" in cookie_header:
                csrf_cookie_found = True
                assert (
                    "Secure" in cookie_header
                ), f"csrf_access_token missing 'Secure' flag: {cookie_header}"
                # CSRF token is designed to be read by JavaScript, so HttpOnly should be false
                assert (
                    "HttpOnly" not in cookie_header
                ), f"csrf_access_token should NOT have 'HttpOnly' flag: {cookie_header}"
                assert (
                    "SameSite=Lax" in cookie_header
                    or "SameSite=Strict" in cookie_header
                    or "SameSite=None" in cookie_header
                ), f"csrf_access_token missing SameSite attribute: {cookie_header}"
                break
        assert csrf_cookie_found, "csrf_access_token not found in response headers"
