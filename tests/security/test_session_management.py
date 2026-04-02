import pytest
from flask import json


class TestSessionManagement:
    """
    Integration tests for stateful session management (Phase 3).
    These tests verify that the system correctly enforces 'Newest Session Wins'
    and performant token revocation using Redis.
    """

    def test_multi_device_invalidation_newest_wins(self, client, setup_users):
        """
        Verify that logging in on a second device invalidates the session
        on the first device.
        """
        admin_user, _ = setup_users
        credentials = {"username": admin_user.username, "password": "testpassword"}

        # 1. Login on Device 1
        resp1 = client.post("/api/auth/login", json=credentials)
        assert resp1.status_code == 200

        # Capture refresh token from Device 1
        refresh_token1 = None
        for cookie in resp1.headers.getlist("Set-Cookie"):
            if "refresh_token_cookie" in cookie:
                refresh_token1 = cookie.split("=")[1].split(";")[0]
                break
        assert refresh_token1 is not None

        # 2. Login on Device 2 (Same User)
        resp2 = client.post("/api/auth/login", json=credentials)
        assert resp2.status_code == 200

        # 3. Attempt to use Device 1's refresh token to get a new access token
        client.set_cookie("refresh_token_cookie", refresh_token1)

        csrf_token1 = None
        for cookie in resp1.headers.getlist("Set-Cookie"):
            if "csrf_refresh_token" in cookie:
                csrf_token1 = cookie.split("=")[1].split(";")[0]
                break

        headers = {}
        if csrf_token1:
            headers["X-CSRF-TOKEN"] = csrf_token1

        refresh_resp = client.post("/api/auth/refresh", headers=headers)

        # 4. Assert: Device 1's session should now be rejected
        assert refresh_resp.status_code == 401
        data = refresh_resp.get_json()
        assert data["error_code"] == "UNAUTHORIZED"
        # Accept framework default or custom message
        assert any(
            term in data["message"].lower()
            for term in ["session", "expired", "invalid", "revoked"]
        )

    def test_logout_invalidates_session(self, client, setup_users):
        """
        Verify that explicitly logging out invalidates the user's session in Redis,
        preventing further use of the refresh token.
        """
        admin_user, _ = setup_users
        credentials = {"username": admin_user.username, "password": "testpassword"}

        # 1. Login to get a session
        login_resp = client.post("/api/auth/login", json=credentials)
        assert login_resp.status_code == 200

        # Extract tokens
        refresh_token = None
        access_token = None
        csrf_token = None
        for cookie in login_resp.headers.getlist("Set-Cookie"):
            if "refresh_token_cookie" in cookie:
                refresh_token = cookie.split("=")[1].split(";")[0]
            if "access_token_cookie" in cookie:
                access_token = cookie.split("=")[1].split(";")[0]
            if "csrf_access_token" in cookie:
                csrf_token = cookie.split("=")[1].split(";")[0]

        assert refresh_token is not None
        assert access_token is not None

        # 2. Perform Logout
        # Must send access token + CSRF to logout
        client.set_cookie("access_token_cookie", access_token)
        headers = {}
        if csrf_token:
            headers["X-CSRF-TOKEN"] = csrf_token

        logout_resp = client.post("/api/auth/logout", headers=headers)
        assert logout_resp.status_code == 200

        # 3. Attempt to use the refresh token from the logged-out session
        client.set_cookie("refresh_token_cookie", refresh_token)
        # We need the refresh CSRF token too
        csrf_refresh_token = None
        for cookie in login_resp.headers.getlist("Set-Cookie"):
            if "csrf_refresh_token" in cookie:
                csrf_refresh_token = cookie.split("=")[1].split(";")[0]

        headers = {}
        if csrf_refresh_token:
            headers["X-CSRF-TOKEN"] = csrf_refresh_token

        refresh_attempt_resp = client.post("/api/auth/refresh", headers=headers)

        # 4. Assert: The refresh attempt should be rejected
        assert refresh_attempt_resp.status_code == 401
        data = refresh_attempt_resp.get_json()
        assert data["error_code"] == "UNAUTHORIZED"
        assert any(
            term in data["message"].lower()
            for term in ["session", "expired", "invalid", "revoked"]
        )
