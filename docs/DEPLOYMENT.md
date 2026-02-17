# Deployment & CI/CD

This document covers the current deployment flow, CI/CD, runner expectations, and environment configuration for the project.

## Overview
-   **CI/CD System:** GitHub Actions
-   **CI/Test Environment:** Runs on GitHub-hosted `ubuntu-latest` for build and initial testing.
-   **Staging Deployment:** Deploys to a self-hosted WSL runner using `scripts/deploy.sh`.
-   **Production Deployment (Future):** Will deploy to a self-hosted Raspberry Pi runner (ARM architecture).
-   **Architecture:** Nginx terminates TLS (HTTPS) and proxies to the Flask API (Gunicorn). Docker Compose manages all services.

## Environment Configuration
**Source of Configuration Values**
Configuration values are sourced in a hierarchical manner:

1.  **GitHub Secrets:** Used for all sensitive information (e.g., `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`). These are injected directly into the CI/CD environment and passed to containers.
2.  **`docker-compose.yml`:** This is the primary source for all non-secret default environment variables (e.g., `LOG_LEVEL`, `GUNICORN_WORKERS`). It defines the base services and contains the `build: .` context for the `web` service for local development.
3.  **`docker-compose.ci.yml`:** This is an override file used *only* in CI/CD. It overrides the `web` service definition from `docker-compose.yml` to specify `image: ${IMAGE_TAG}` and `build: null`, ensuring that CI/Staging pulls a pre-built image from the registry.
4.  **`docker-compose.override.yml`:** This is an override file (generated from `docker-compose.override.yml.template`) used *only* for local development. It sets up volume mounts for live reloading, development-specific environment variables (e.g., `FLASK_ENV=development`), and exposes additional ports.
5.  **`.env` file (Local Development Only):** Used for local overrides and sensitive secrets that are not committed to Git. It should define `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and any optional overrides. **It is NOT used in the CI/CD pipeline.**
6.  **`config.env` file (Local Development Reference):** Defines shared non-secret defaults. It is used as a reference for local `.env` files but is **not used by the CI/CD pipeline.**
7.  **`IMAGE_TAG` (CI/CD Only):** Set by the workflow (lowercased) and used by `docker-compose.ci.yml` and `scripts/deploy.sh` to pull the pre-built image.

## CI Pipeline (dev branch)
**Workflow:** `.github/workflows/test-deploy.yml`
**Trigger:** `push` events to `dev` or `main` branches.
**Runs on:** `ubuntu-latest`

**Key Steps:**
1.  **Checkout Code:** Retrieves the repository content.
2.  **Setup QEMU & Docker Buildx:** Prepares the environment for multi-platform Docker builds.
3.  **Login to GitHub Container Registry (`ghcr.io`):** Authenticates Docker with `ghcr.io` using `GITHUB_TOKEN` to allow pushing and pulling images.
4.  **Generate Self-Signed Certificates (CI Only):** Creates temporary SSL certificates for the Nginx service within the CI environment.
5.  **Build and Push Multi-platform Docker Image:** Builds the `web` service image for `linux/amd64` and `linux/arm64` platforms, then pushes the multi-architecture image manifest to `ghcr.io/<owner>/<repo>:latest` (derived from `IMAGE_TAG`).
6.  **Start Containers:** Uses `docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --wait --pull always --no-build` to start `mongo`, `redis`, and `web`. It pulls the `web` image from `ghcr.io` (via `docker-compose.ci.yml`) and waits for all services (including the `web` service's health check) to become `healthy`.
7.  **Seed Database:** Executes `scripts/seed_db.py` to populate the database with initial data.
8.  **Inject and Run Tests:** Copies test files into the running `web` container and executes `pytest`.
9.  **Teardown:** Stops and removes all services created by Docker Compose.

## Staging Deployment (WSL Runner)
**Triggered by:** Runs after the `build-and-test` job successfully completes.
**Runs on:** A self-hosted runner explicitly labeled `wsl-staging`.

**Key Steps:**
1.  **Checkout Code:** Retrieves the repository content.
2.  **Make Deploy Script Executable:** Ensures `scripts/deploy.sh` can be run.
3.  **Validate Required Secrets:** Checks for the presence of necessary secrets.
4.  **Deploy to WSL:** Executes `scripts/deploy.sh` which:
    *   Generates self-signed certificates.
    *   Executes `docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --wait --pull always --no-build`. This pulls the `web` image from `ghcr.io` (via `docker-compose.ci.yml`) and starts all services.
    *   Waits for MongoDB service to be healthy.
5.  **Verify Staging Health:** Runs `curl -k -f` check against `https://localhost/` to ensure the application stack is responsive.
6.  **Create Admin & Seed DB:** Sets up the admin user and populates initial data in the staging environment.

## Docker & Application Configuration
*   **Image Source:** `web` service in `docker-compose.yml` is `build: .` (for local dev). For CI/Staging, `docker-compose.ci.yml` overrides this to `image: ${IMAGE_TAG}` and disables build (pulled from `ghcr.io`). `mongo` and `redis` use their respective official Docker Hub images.
*   **Configurable Gunicorn Workers:** The `web` service's `Dockerfile` uses `${GUNICORN_WORKERS}` to set the number of Gunicorn worker processes. `docker-compose.yml` provides a safe default (e.g., `3`) via `GUNICORN_WORKERS: ${GUNICORN_WORKERS:-3}`.
*   **Flask App Env:** `FLASK_ENV` is set to `development` for CI/test and `production` for staging/deployment.
*   **Talisman/HTTPS:** `TALISMAN_FORCE_HTTPS` is configured (default `true` for deployment).
*   **ProxyFix:** `PROXY_FIX_X_FOR`, `PROXY_FIX_X_PROTO`, etc., are configured to handle reverse proxy headers.
*   **Service Health Checks:** `mongo`, `redis`, and the `web` (Flask) services all have `healthcheck` definitions in `docker-compose.yml`.

## Certificates
*   Nginx expects SSL certificates at `./certs/server.crt` and `./certs/server.key`.
*   Self-signed certificates are generated by CI/`scripts/deploy.sh` for development and staging environments.
*   Production certificates (e.g., from Cloudflare) can replace these by placing them in the `./certs` folder.

## Runners & Permissions
*   **WSL Staging Runner:** Must have Docker access and be registered with the label `wsl-staging`.
*   **Production Raspberry Pi Runner (Future):** Will be ARM-based and utilize the `ghcr.io` multi-platform image.
*   Deployment avoids `sudo` within containers by using unprivileged `appuser` and container-based ownership fixes.

## Notes
*   Keep Mongo/Redis ports internal within the Docker network unless explicit exposure is required for local debugging.
*   `docker-compose.yml` is the primary source for non-secret environment defaults (when building locally). `docker-compose.ci.yml` overrides image sourcing for CI/CD.

## Workflow Preflight (Local)
To avoid trial-and-error on GitHub, run a local preflight before pushing:

1.  **Lint workflows (fast):**
    ```powershell
    .\scripts\preflight_ci.ps1
    ```
    This uses `actionlint` to validate `.github/workflows/*.yml` and catches expression errors (e.g., invalid functions).

2.  **Run a local workflow (optional, slower):**
    ```powershell
    .\scripts\preflight_ci.ps1 -RunAct
    ```
    This uses `act` to execute the workflow locally.

If `actionlint` or `act` is missing, the script will print a hint to install them.

## Local CI Simulation
To simulate the CI flow locally (without pushing to GHCR), build the image locally, set `IMAGE_TAG` to the local image name, and run with the CI override:

1.  `docker compose -f docker-compose.yml build --build-arg LOG_LEVEL=INFO`
2.  `set IMAGE_TAG=<local-image-tag>` (PowerShell: `$env:IMAGE_TAG="flaskweb_project_root-web:latest"`)
3.  `docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --wait --no-build`

This mirrors the CI path (compose override + no build) while using a locally built image. For true registry validation, you must pull the image from `ghcr.io` and keep `--pull always`.
