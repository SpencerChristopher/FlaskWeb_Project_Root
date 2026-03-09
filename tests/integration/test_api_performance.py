import pytest
import time
import requests
import os
import urllib3
import socket

# Use local certificate for verification if it exists to avoid warnings
CERT_PATH = "/app/certs/server.crt" if os.getenv("DOCKER_CONTAINER") == "true" else "certs/server.crt"
VERIFY = CERT_PATH if os.path.exists(CERT_PATH) else False

# Setup session
session = requests.Session()

# Force resolution of 'localhost' to the nginx IP globally within this process
# to allow certificate verification (which expects 'localhost') while 
# networking connects to the 'nginx' service.
if os.getenv("DOCKER_CONTAINER") == "true" and VERIFY:
    try:
        nginx_ip = socket.gethostbyname("nginx")
        original_getaddrinfo = socket.getaddrinfo
        def patched_getaddrinfo(*args, **kwargs):
            if args[0] == "localhost":
                # Route localhost requests to nginx container IP
                return original_getaddrinfo(nginx_ip, *args[1:], **kwargs)
            return original_getaddrinfo(*args, **kwargs)
        socket.getaddrinfo = patched_getaddrinfo
    except Exception:
        pass

# Only suppress warnings if we are NOT verifying
if not VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@pytest.mark.performance
class TestAPIPerformance:
    """
    Integration tests to ensure API responsiveness.
    Targets under 200ms for core endpoints to ensure 'snappy' feel.
    """

    def _get_base_url(self, prod_base_url):
        if os.getenv("DOCKER_CONTAINER") == "true" and VERIFY:
            return "https://localhost"
        return prod_base_url

    def test_bootstrap_latency(self, prod_base_url):
        """
        Verify that the bootstrap endpoint (combined Auth + Profile)
        responds within the performance budget.
        """
        base = self._get_base_url(prod_base_url)
        url = f"{base}/api/bootstrap"

        # Measure 5 samples to get an average
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            resp = session.get(url, verify=VERIFY)
            end = time.perf_counter()
            assert resp.status_code == 200
            latencies.append((end - start) * 1000)  # Convert to ms

        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage Bootstrap Latency: {avg_latency:.2f}ms")

        # Threshold: 200ms for initial combined load
        assert avg_latency < 200, f"Bootstrap API too slow: {avg_latency:.2f}ms"

    def test_blog_list_latency(self, prod_base_url):
        """
        Verify that the blog listing (paginated) responds efficiently.
        """
        base = self._get_base_url(prod_base_url)
        url = f"{base}/api/blog?page=1&per_page=6"

        start = time.perf_counter()
        resp = session.get(url, verify=VERIFY)
        end = time.perf_counter()

        latency = (end - start) * 1000
        assert resp.status_code == 200
        print(f"Blog List Latency: {latency:.2f}ms")

        # Threshold: 150ms for paginated list
        assert latency < 150, f"Blog List API too slow: {latency:.2f}ms"
