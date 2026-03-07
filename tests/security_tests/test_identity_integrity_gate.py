import pytest
from unittest.mock import MagicMock, patch
from src.services.profile_service import ProfileService
from src.schemas import UserIdentity

class TestIdentityIntegrityGate:
    """
    Gating tests to verify architectural consistency and auditability.
    These tests identify the 'Identity Leak' and 'Side-Door' patterns.
    """

    def test_profile_update_route_consistency(self, client):
        """
        Gate: All protected PUT routes should return 401 for unauthenticated requests
        with a consistent error shape.
        """
        resp = client.put("/api/content/profile", json={"name": "Hacker"})
        
        # If this fails with 405 or a different error, the side-door issue is proven.
        assert resp.status_code == 401, "Protected route failed to return 401 for unauthenticated PUT"
        assert "error_code" in resp.get_json()

    def test_profile_service_requires_user_identity(self, app):
        """
        Gate: The service layer should not allow updates without identity context.
        Current implementation fails this gate because it doesn't accept 'user'.
        """
        from src.services import get_profile_service
        
        with app.app_context():
            svc = get_profile_service()
            
            # We check the signature of update_profile
            import inspect
            sig = inspect.signature(svc.update_profile)
            
            # FAIL POINT: If 'user' is not in parameters, the architecture is leaky.
            assert 'user' in sig.parameters, "ProfileService.update_profile is missing identity context (Audit Leak)"

    def test_bootstrap_capabilities_alignment(self, client, admin_headers, user_headers):
        """
        Gate: Verify that /api/bootstrap returns capabilities aligned with the Authorization Matrix.
        """
        # 1. Admin Capabilities
        resp = client.get("/api/bootstrap", headers=admin_headers)
        data = resp.get_json()
        caps = data['auth']['user']['capabilities']
        assert "profile:manage" in caps
        assert "content:manage" in caps

        # 2. Member Capabilities (Should be empty or read-only)
        resp = client.get("/api/bootstrap", headers=user_headers)
        data = resp.get_json()
        caps = data['auth']['user']['capabilities']
        assert "profile:manage" not in caps
        assert "content:manage" not in caps
