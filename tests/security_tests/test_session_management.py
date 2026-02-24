import pytest
from flask import json
import re

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
        # (This should trigger session invalidation for Device 1 in implementation)

        # 3. Attempt to use Device 1's refresh token to get a new access token
        # We manually set the cookie to simulate the old device's state
        client.set_cookie("refresh_token_cookie", refresh_token1)
        
        # We also need the CSRF token for the refresh request if CSRF is enabled for refresh
        # (Assuming it follows the same pattern as access tokens)
        csrf_token1 = None
        for cookie in resp1.headers.getlist("Set-Cookie"):
            if "csrf_refresh_token" in cookie: # flask-jwt-extended default
                csrf_token1 = cookie.split("=")[1].split(";")[0]
                break
        
        headers = {}
        if csrf_token1:
            headers["X-CSRF-TOKEN"] = csrf_token1

        refresh_resp = client.post("/api/auth/refresh", headers=headers)

        # 4. Assert: Device 1's session should now be rejected
        # This will currently FAIL because session proofing isn't implemented.
        assert refresh_resp.status_code == 401, "Old session should have been invalidated by new login."
        data = refresh_resp.get_json()
        assert data["error_code"] == "UNAUTHORIZED"
        assert "session has expired" in data["message"].lower() or "revoked" in data["message"].lower()
