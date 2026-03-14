# Troubleshooting Guide

This guide captures known test failures and their root causes, with concrete fixes. Keep it updated as new issues are found.

## Local E2E (Host Venv)

### 1. Login succeeds but UI stays guest
**Symptom:** Login returns 200, but admin nav never appears; e2e waits for "Edit Profile".  
**Root cause:** Secure cookies are not sent over HTTP.  
**Fix:** Ensure local overrides disable HTTPS/security cookies:
- `TALISMAN_FORCE_HTTPS=false`
- `JWT_COOKIE_SECURE=false`

### 2. Playwright fails after container recreate
**Symptom:** `BrowserType.launch: Executable doesn't exist ...`  
**Root cause:** Playwright browser binaries are not baked into the image and are wiped on recreate.  
**Fix:** Reinstall locally (host or container depending on where tests run):
```powershell
python -m playwright install chromium
```

### 3. Infinite scroll test only sees 2 articles
**Symptom:** `test_blog_infinite_scroll` expects 6 cards but only sees 2.  
**Root cause:** Database seeded with only the base articles.  
**Fix:** Seed heavy data set:
```powershell
docker compose exec web /app/.venv/bin/python scripts/seed_db.py --heavy
```

### 4. `base_url` is empty or tests navigate to `/home` without a host
**Symptom:** `Page.goto: Cannot navigate to invalid URL` or base URL is blank.  
**Root cause:** `pytest-base-url` not configured.  
**Fix:** Set `PYTEST_BASE_URL` or `E2E_BASE_URL`:
```powershell
$env:PYTEST_BASE_URL="http://localhost:5005"
$env:E2E_BASE_URL="http://localhost:5005"
```

---

## Container Tests (CI Parity)

### 1. `http://nginx` redirects to HTTPS and then fails
**Symptom:** Playwright hits `http://nginx` and gets `ERR_CONNECTION_REFUSED` on redirect.  
**Root cause:** `TALISMAN_FORCE_HTTPS=true` in local config while nginx only serves HTTP.  
**Fix:** Use local overrides:
- `TALISMAN_FORCE_HTTPS=false`
- `JWT_COOKIE_SECURE=false`

### 2. E2E base URL mismatch
**Symptom:** Connection refused to `localhost` inside container.  
**Root cause:** Running e2e inside Docker without overriding base URL.  
**Fix:** Use service DNS:
```bash
docker compose exec -e E2E_BASE_URL=http://nginx -e PYTEST_BASE_URL=http://nginx web /app/.venv/bin/pytest /app/tests
```

### 3. HTTPS-only tests fail in local container
**Symptom:** `test_https_redirection_deep` or secure cookie tests fail.  
**Root cause:** HTTPS-only checks don’t apply to local HTTP.  
**Fix:** Skip unless explicitly enforcing HTTPS:
```bash
REQUIRE_HTTPS=1  # only when testing behind HTTPS (staging)
```

---

## Staging (Cloudflare Access)

### 1. 403/401 from staging
**Symptom:** Smoke/e2e tests fail with auth errors.  
**Root cause:** Missing or incorrect Cloudflare Access headers.  
**Fix:** Set service token env vars:
- `CF_ACCESS_CLIENT_ID`
- `CF_ACCESS_CLIENT_SECRET` (or `CF_ACCESS_JWT`)

### 2. HTTPS-only checks skipped unexpectedly
**Symptom:** HTTPS security tests are skipped during staging run.  
**Root cause:** `REQUIRE_HTTPS` not set.  
**Fix:**
```bash
export REQUIRE_HTTPS=1
```

---

## Quick Diagnostics

### Check nginx reachability from container
```bash
docker compose exec web /app/.venv/bin/python -c "import http.client as c; conn=c.HTTPConnection('nginx',80,timeout=5); conn.request('GET','/'); print(conn.getresponse().status)"
```

### Validate login status via API
```bash
docker compose exec web /app/.venv/bin/python -c "import os,requests; s=requests.Session(); base='http://nginx'; s.post(f'{base}/api/auth/login', json={'username':os.environ.get('ADMIN_USERNAME','admin'),'password':os.environ.get('ADMIN_PASSWORD','NewAdmin2020!')}); print(s.get(f'{base}/api/auth/status').text)"
```
