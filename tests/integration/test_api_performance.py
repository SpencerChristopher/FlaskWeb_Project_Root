import pytest
import time
import requests
import os

@pytest.mark.performance
class TestAPIPerformance:
    """
    Integration tests to ensure API responsiveness.
    Targets under 200ms for core endpoints to ensure 'snappy' feel.
    """

    def test_bootstrap_latency(self):
        """
        Verify that the bootstrap endpoint (combined Auth + Profile) 
        responds within the performance budget.
        """
        url = "https://127.0.0.1/api/bootstrap"
        
        # Measure 5 samples to get an average
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            resp = requests.get(url, verify=False)
            end = time.perf_counter()
            assert resp.status_code == 200
            latencies.append((end - start) * 1000) # Convert to ms
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage Bootstrap Latency: {avg_latency:.2f}ms")
        
        # Threshold: 200ms for initial combined load
        assert avg_latency < 200, f"Bootstrap API too slow: {avg_latency:.2f}ms"

    def test_blog_list_latency(self):
        """
        Verify that the blog listing (paginated) responds efficiently.
        """
        url = "https://127.0.0.1/api/blog?page=1&per_page=6"
        
        start = time.perf_counter()
        resp = requests.get(url, verify=False)
        end = time.perf_counter()
        
        latency = (end - start) * 1000
        assert resp.status_code == 200
        print(f"Blog List Latency: {latency:.2f}ms")
        
        # Threshold: 150ms for paginated list
        assert latency < 150, f"Blog List API too slow: {latency:.2f}ms"
