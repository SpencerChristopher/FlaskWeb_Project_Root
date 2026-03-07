import concurrent.futures
import requests
import time
import statistics
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def make_request(url):
    start = time.perf_counter()
    try:
        resp = requests.get(url, verify=False, timeout=10)
        latency = (time.perf_counter() - start) * 1000
        return latency, resp.status_code
    except Exception as e:
        return (time.perf_counter() - start) * 1000, 500

def run_load_test(url, concurrent_users, total_requests):
    print(f"\n--- Testing {concurrent_users} Concurrent Users ({total_requests} total requests) ---")
    
    latencies = []
    status_codes = []
    
    start_test = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_request, url) for _ in range(total_requests)]
        for future in concurrent.futures.as_completed(futures):
            lat, status = future.result()
            latencies.append(lat)
            status_codes.append(status)
            
    total_time = time.perf_counter() - start_test
    rps = total_requests / total_time
    
    avg_lat = sum(latencies) / len(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18] # 95th percentile
    
    success_rate = (status_codes.count(200) / total_requests) * 100
    
    print(f"RPS: {rps:.2f}")
    print(f"Average Latency: {avg_lat:.2f}ms")
    print(f"p95 Latency: {p95_lat:.2f}ms")
    print(f"Success Rate: {success_rate:.1f}%")
    
    return {
        "users": concurrent_users,
        "rps": rps,
        "p95": p95_lat,
        "fail": status_codes.count(500)
    }

if __name__ == "__main__":
    TARGET_URL = "https://127.0.0.1/api/bootstrap"
    
    results = []
    # Ramp up to find the breaking point
    for users in [1, 5, 20, 50]:
        res = run_load_test(TARGET_URL, users, total_requests=100)
        results.append(res)
        
    print("\n--- Saturation Summary ---")
    print("Users | RPS    | p95 Latency")
    for r in results:
        print(f"{r['users']:5} | {r['rps']:6.2f} | {r['p95']:8.2f}ms")
