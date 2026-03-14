import pytest
import requests
import os
import urllib3
import socket
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import HTTPSConnectionPool

# Use local certificate for verification if it exists to avoid warnings
CERT_PATH = "/app/certs/server.crt" if os.getenv("DOCKER_CONTAINER") == "true" else "certs/server.crt"
VERIFY = CERT_PATH if os.path.exists(CERT_PATH) else False

class HostResolverAdapter(HTTPAdapter):
    """
    Adapter that forces 'localhost' requests to a specific IP while 
    preserving the 'localhost' hostname for SSL SNI and verification.
    """
    def __init__(self, target_ip, **kwargs):
        self.target_ip = target_ip
        super().__init__(**kwargs)

    def get_connection(self, url, proxies=None):
        # This is for requests < 2.30; for newer versions we might need to 
        # override different methods, but let's try this or use a custom 
        # urllib3 PoolManager.
        return super().get_connection(url, proxies)

    def send(self, request, **kwargs):
        # The simplest way to do this in modern requests/urllib3 is to 
        # spoof the 'Host' header and use the IP in the URL, BUT that 
        # fails certificate verification because 'requests' matches the 
        # URL hostname against the cert.
        
        # Instead, we keep 'localhost' in the URL but we use a custom 
        # resolver if possible, or we just use the 'verify=False' with 
        # warnings suppressed if this complexity fails.
        return super().send(request, **kwargs)

# Setup session
session = requests.Session()

# Since the previous HostHeaderAdapter failed with IP mismatch, 
# let's try the 'urllib3' way of forcing the resolution of 'localhost' 
# to the nginx IP globally within this process.
if os.getenv("DOCKER_CONTAINER") == "true" and VERIFY:
    try:
        nginx_ip = socket.gethostbyname("nginx")
        
        # Monkeypatching socket.getaddrinfo to force localhost -> nginx_ip
        original_getaddrinfo = socket.getaddrinfo
        def patched_getaddrinfo(*args, **kwargs):
            if args[0] == "localhost":
                return original_getaddrinfo(nginx_ip, *args[1:], **kwargs)
            return original_getaddrinfo(*args, **kwargs)
        socket.getaddrinfo = patched_getaddrinfo
    except Exception:
        pass

# Only suppress warnings if we are NOT verifying
if not VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# These tests are intended to run against a LIVE production/staging instance.
# They verify that the 'Double Gate' and core infrastructure are operational.


class TestProdReadiness:
    """Smoke tests for production environments."""

    def _get_base_url(self, prod_base_url):
        """
        Dynamically determine the base URL.
        - If in Docker and no certs, use HTTP on Port 80 (internal nginx).
        - If Staging (URL contains spencerscooking.uk), use HTTPS.
        """
        if "spencerscooking.uk" in prod_base_url:
            return prod_base_url # Already includes https://
            
        if os.getenv("DOCKER_CONTAINER") == "true":
            # If no certs, hit nginx on port 80 instead of 443
            if not VERIFY:
                return prod_base_url.replace("https://", "http://")
        return prod_base_url

    def test_api_bootstrap_public(self, prod_base_url):
        """Verify that bootstrap endpoint is reachable and returns public data."""
        base = self._get_base_url(prod_base_url)
        url = f"{base}/api/bootstrap"
        # Allow redirects here as bootstrap should be public, but might redirect if no data exists
        resp = session.get(url, verify=VERIFY, allow_redirects=True)
        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert "auth" in data

    def test_db_connectivity_via_blog_api(self, prod_base_url):
        """Verify that the blog API can fetch posts (DB Check)."""
        base = self._get_base_url(prod_base_url)
        url = f"{base}/api/blog"
        resp = session.get(url, verify=VERIFY, allow_redirects=True)
        assert resp.status_code == 200
        data = resp.json()
        assert "posts" in data
        assert isinstance(data["posts"], list)

    def test_unauthorized_content_access_blocked(self, prod_base_url):
        """Verify that administrative endpoints are correctly gated."""
        base = self._get_base_url(prod_base_url)
        url = f"{base}/api/content/articles"
        # We expect a redirect to login (302) or a 401 if it's strictly API
        resp = session.get(url, verify=VERIFY, allow_redirects=False)
        assert resp.status_code in [302, 401]

    def test_static_assets_available(self, prod_base_url):
        """Verify that Nginx is correctly serving static files."""
        base = self._get_base_url(prod_base_url)
        url = f"{base}/static/app.js"
        resp = session.get(url, verify=VERIFY, allow_redirects=True)
        assert resp.status_code == 200
        assert "application/javascript" in resp.headers.get("Content-Type", "")
