# Flask Web Project

## Description

This project is a personal website and blog built with Flask and MongoDB, featuring a decoupled frontend and a JSON-based API. The backend leverages **Pydantic** for robust data validation, **Blinker** for a signal-based event-driven architecture, and **JWT** for secure authentication. The frontend is a vanilla JavaScript Single Page Application (SPA).

## Features

*   **API-First Design**: A comprehensive JSON API serves all public and administrative content.
*   **Pydantic Validation**: All API inputs strictly validated using Pydantic models.
*   **Event-Driven Architecture**: Utilizes **Blinker** for decoupled application logic.
*   **User Authentication**: Secure JWT-based login with RBAC.
*   **Security Hardening**: Rate limiting, HTML sanitization, and HTTPS proxying.
*   **Hardware Optimized**: Tuned for high stability on **2GB Raspberry Pi (ARM64)**.
*   **Dockerized Environment**: Consistent setup and deployment via isolated environment lanes.

## Technologies Used

*   **Backend**: Flask (Python), MongoDB, Redis
*   **Frontend**: Vanilla JS (SPA), CSS, HTML
*   **DevOps**: Docker, Nginx, Poetry, GitHub Actions, Multi-platform (AMD64/ARM64) Verification

---

## Setup with Docker (Recommended)

The project is fully containerized for consistent development and deployment. Nginx terminates HTTPS on `:443` and proxies to the Flask API.

### 1. Prerequisites
*   Docker Desktop (with Compose)
*   GitHub CLI (`gh`) - Required for configuration sync.
*   Python 3.11+ (if running host-side tests)

### 2. Configuration & Secrets
Configuration is decoupled into **Secrets** (sensitive) and **Variables** (behavioral).
1.  **Secrets**: Create your local `.env`: `cp .env.template .env` and add your keys.
2.  **Variables**: Sync latest behavior settings from GitHub:
    ```powershell
    powershell.exe -File scripts/sync_vars.ps1
    ```
    This generates `.env.vars` which is used by the local stack.
3.  **Overrides**: Initialize your local dev overrides: `cp docker-compose.override.yml.template docker-compose.override.yml`

For a detailed explanation of the environment variable hierarchy, see [Deployment Guide](docs/DEPLOYMENT.md).

### 3. Quick Start
```bash
# Build and start services (Uses isolated Port 5010)
docker compose --env-file .env --env-file .env.vars up --build -d

# Seed the database
docker compose exec web /app/.venv/bin/python scripts/seed_db.py
```

The application will be available locally at `http://localhost:5010`.

---

## Development & Testing

Comprehensive documentation for developing and verifying the system is available in the `docs/` folder:

*   **[Testing Strategy](docs/TESTING.md)**: How to run unit, integration, and E2E tests in both local and container environments.
*   **[Deployment & CI/CD](docs/DEPLOYMENT.md)**: Details on the automated pipeline, environment injection, and production architecture.
*   **[API Contract](docs/api-contract.yml)**: OpenAPI specification for the backend service.

### Quick Test Execution
```bash
# Run backend tests inside the container
docker compose exec web /app/.venv/bin/pytest tests/ -m "not e2e"
```

### E2E Testing (Local & Staging)
Local E2E (host-side):
```powershell
# Start stack (uses .env + .env.vars)
docker compose --env-file .env --env-file .env.vars up -d

# Run E2E from host venv
$env:SKIP_DB_CHECK="1"
python -m pytest tests/e2e -m e2e -p no:flask
```

Staging E2E (Cloudflare Access):
```powershell
$env:E2E_BASE_URL="https://staging.spencerscooking.uk"
$env:PROD_BASE_URL="https://staging.spencerscooking.uk"
$env:REQUIRE_HTTPS="1"
$env:REQUIRE_CF_ACCESS="1"
$env:CF_ACCESS_CLIENT_ID="<token>"
$env:CF_ACCESS_CLIENT_SECRET="<secret>"
python -m pytest tests/e2e -m e2e
```

Notes:
* Staging data is stable and is not reseeded on push.
* If you need a fresh dataset, trigger a manual workflow with `reseed_db` or `heavy_seed`.
* Set `REQUIRE_HEAVY_SEED=1` if you want infinite-scroll E2E to hard-fail when the dataset is too small.

## Project Structure

```
. # Project Root
+-- src/                      # Main application source code
+-- scripts/                  # Utility scripts (seeding, admin creation, sync)
+-- static/                   # Frontend static files (JS, CSS)
+-- templates/                # Base Jinja2 template for the SPA shell
+-- docker/                   # Docker assets (nginx config, mongo init)
+-- docs/                     # Architectural and workflow documentation
+-- tests/                    # Test suites (unit, integration, e2e)
+-- certs/                    # TLS certs (self-signed for dev/CI)
+-- .env.template             # Template for .env
+-- docker-compose.yml        # Main Docker Compose (Base configuration)
+-- Dockerfile                # Dockerfile for the Flask application
+-- main.py                   # Main application entry point
+-- pyproject.toml            # Poetry project configuration
+-- README.md                 # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   Special thanks to Google and the Gemini team for the development and assistance provided through the Gemini CLI.
