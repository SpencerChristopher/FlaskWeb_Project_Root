# Testing Strategy & Execution Guide

This document defines the standards for verifying the Flask Web Project. It distinguishes between continuous development testing and pre-push validation (Preflight).

## 1. Execution Environments

The project supports two testing perspectives. Choosing the wrong one will cause network failures for integration and smoke tests.

### A. Host-Side Testing (Standard)
Run from your local terminal/IDE.
*   **Target:** `https://localhost` (via Nginx proxy)
*   **Scope:** Best for E2E (Playwright) and quick iterative unit tests.
*   **Command:** 
    ```powershell
    # End-to-End (Requires Playwright installed on host)
    $env:SKIP_DB_CHECK="1"; python -m pytest tests/e2e/ --base-url https://localhost -p no:flask
    ```

### B. Container-Side Testing (CI Parity)
Run from inside the `web` container.
*   **Target:** `https://nginx` (Internal Docker network)
*   **Scope:** Best for verifying integration, infrastructure risks (chaos), and performance benchmarks.
*   **Requirement:** The container detects it is inside Docker and automatically switches routing.
*   **Command:** 
    ```bash
    docker compose exec -T web /app/.venv/bin/pytest tests/ -m "not e2e"
    ```

---

## 2. Testing vs. Preflight

| Tool | Purpose | Frequency | Context |
| :--- | :--- | :--- | :--- |
| **Pytest** | Functional validation, TDD, and debugging. | **Always** during dev. | Local/Container |
| **Preflight** | Final gatekeeper. Checks linting, audit logs, and CI parity. | **Before Push** only. | Host (calls Docker) |

**Note:** Do not use `scripts/preflight.sh` as your primary test runner. It performs heavy cleanup and environment resets that will slow down your development loop.

---

## 3. Special Test Requirements

### A. Accessibility (Axe)
E2E tests include accessibility checks via `axe-core`. To enable these, you must download the script to the local directory:
```bash
curl -L -o tests/axe/axe.min.js https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js
```

### B. Performance & Heavy Tests
Tests marked with `@pytest.mark.heavy` or `@pytest.mark.performance` should ideally be run in the container to avoid host-side network jitter.

### C. Architectural Integrity (Design Gate)
To ensure that code changes do not violate the boundaries defined in `docs/ARCHITECTURE.md`, run the design gate:
```powershell
# Fast, host-side AST scan (No DB or Container needed)
$env:SKIP_DB_CHECK="1"; .venv/Scripts/python.exe -m pytest tests/domain_tests/test_arch_integrity.py -p no:flask -p no:base-url
```

---

## 4. Engineering Standards

### Mocking Standards
To prevent "fragile tests" that break on repository optimizations:
1.  **Mock Interfaces, Not Internals:** Never mock MongoEngine's `Article.objects`. Always mock the **Repository instance** on the service.
    *   *Bad:* `patch('models.Article.objects')`
    *   *Good:* `patch.object(article_service._article_repository, 'get_published_paginated')`
2.  **DTO Trust:** The Service layer trusts the `UserIdentity` DTO provided by the Authorization layer. Unit tests for services should mock the `AuthzService` result rather than expecting the service to re-validate user existence.

### The "Double Gate" Pattern
Authorization is enforced twice:
1.  **Stateless Gate:** Permissions are derived from JWT claims for speed.
2.  **Stateful Gate:** Role and Token Version are verified against the DB for security.
Tests verifying access must account for both gates.

---

## 5. Common Pitfalls

*   **401 Unauthorized in E2E:** Usually caused by a `SECRET_KEY` mismatch between the Host `.env` and the Container environment. Ensure they match.
*   **Connection Refused (Container):** Occurs if a test tries to hit `localhost` while running inside the container. Use the `prod_base_url` fixture which handles this automatically.
