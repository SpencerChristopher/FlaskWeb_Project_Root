# Flask Web Project

## Description

This project is a personal website and blog built with Flask and MongoDB, featuring a decoupled frontend and a JSON-based API. The backend leverages **Pydantic** for robust data validation, **Blinker** for a signal-based event-driven architecture, and **JWT** for secure authentication. The frontend is a vanilla JavaScript Single Page Application (SPA).

## Features

*   **API-First Design**: A comprehensive JSON API serves all public and administrative content.
*   **Pydantic Validation**: All API inputs strictly validated using Pydantic models.
*   **Event-Driven Architecture**: Utilizes **Blinker** for decoupled application logic.
*   **User Authentication**: Secure JWT-based login with RBAC.
*   **Security Hardening**: Rate limiting, HTML sanitization, and HTTPS proxying.
*   **Dockerized Environment**: Consistent setup and deployment via Docker Compose.

## Technologies Used

*   **Backend**: Flask (Python), MongoDB, Redis
*   **Frontend**: Vanilla JS (SPA), CSS, HTML
*   **DevOps**: Docker, Nginx, Poetry, GitHub Actions, Multi-platform (AMD64/ARM64) Verification

---

## Setup with Docker (Recommended)

The project is fully containerized for consistent development and deployment. Nginx terminates HTTPS on `:443` and proxies to the Flask API.

### 1. Prerequisites
*   Docker Desktop (with Compose)
*   Python 3.11+ (if running host-side tests)

### 2. Configuration & Secrets
For local development, secrets and overrides are managed via a `.env` file.
1. Create your local `.env`: `cp .env.template .env`
2. Update `.env` with your secrets (`SECRET_KEY`, `ADMIN_PASSWORD`, etc.).
3. Configure your local dev overrides: `cp docker-compose.override.yml.template docker-compose.override.yml`

For a detailed explanation of the environment variable hierarchy, see [Deployment Guide](docs/DEPLOYMENT.md).

### 3. Quick Start
```bash
# Build and start services
docker compose up --build -d

# Seed the database
docker compose exec web /app/.venv/bin/python scripts/create_admin.py
docker compose exec web /app/.venv/bin/python scripts/seed_db.py
```

The application will be available at `http://localhost:5000`.

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

## Project Structure

```
. # Project Root
+-- src/                      # Main application source code
+-- scripts/                  # Utility scripts (seeding, admin creation)
+-- static/                   # Frontend static files (JS, CSS)
+-- templates/                # Base Jinja2 template for the SPA shell
+-- docker/                   # Docker assets (nginx config, mongo init)
+-- docs/                     # Architectural and workflow documentation
+-- tests/                    # Test suites (unit, integration, e2e)
+-- certs/                    # TLS certs (self-signed for dev/CI)
+-- .env.template             # Template for .env
+-- config.env                # Non-secret defaults shared across envs
+-- docker-compose.yml        # Main Docker Compose (prod-like)
+-- Dockerfile                # Dockerfile for the Flask application
+-- main.py                   # Main application entry point
+-- pyproject.toml            # Poetry project configuration
+-- README.md                 # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   Special thanks to Google and the Gemini team for the development and assistance provided through the Gemini CLI.
