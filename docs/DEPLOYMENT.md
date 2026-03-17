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

1.  **GitHub Secrets:** Used for all sensitive information (e.g., `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD`, `MONGO_APP_USER`, `MONGO_APP_PASSWORD`). These are injected directly into the CI/CD environment and passed to containers.
2.  **`docker-compose.yml`:** This is the primary source for all non-secret default environment variables (e.g., `LOG_LEVEL`, `GUNICORN_WORKERS`). It defines the base services and contains the `build: .` context for the `web` service for local development.
3.  **`docker-compose.ci.yml`:** This is an override file used *only* in CI/CD. It overrides the `web` service definition from `docker-compose.yml` to specify `image: ${IMAGE_TAG}` and `build: null`, ensuring that CI/Staging pulls a pre-built image from the registry.
4.  **`docker-compose.override.yml`:** This is an override file (generated from `docker-compose.override.yml.template`) used *only* for local development. It sets up volume mounts for live reloading, development-specific environment variables (e.g., `FLASK_ENV=development`), and exposes additional ports.
5.  **`.env` file (Local Development Only):** Used for local overrides and sensitive secrets that are not committed to Git. It should define `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD`, `MONGO_APP_USER`, `MONGO_APP_PASSWORD`, and any optional overrides. **It is NOT used in the CI/CD pipeline.**
6.  **`config.env` file (Local Development Reference):** Defines shared non-secret defaults. It is used as a reference for local `.env` files but is **not used by the CI/CD pipeline.**
7.  **`IMAGE_TAG` (CI/CD Only):** Set by the workflow to `ghcr.io/<owner>/<repo>:<GITHUB_SHA>` and used by `docker-compose.ci.yml` and `scripts/deploy.sh` to pull the exact image built for that commit.

## CI Pipeline (dev branch)
**Workflow:** `.github/workflows/test-deploy.yml`
**Trigger:** `push` events to `dev` or `main` branches.

To ensure both reliability and speed, the pipeline is split into four modular jobs across different runners.

### 1. Security & Linting (Static Analysis)
*   **Runner:** `ubuntu-latest` (GitHub-hosted)
*   **Tasks:** Runs `pip-audit` for dependency vulnerabilities and `actionlint` for workflow syntax validation. This job fails fast if there are security or configuration issues.

### 2. Check ARM64 Wheels (Compatibility)
*   **Runner:** `ubuntu-latest` (GitHub-hosted)
*   **Tasks:** Performs a dry-run Docker build specifically for `linux/arm64`.
*   **Rationale:** Uses QEMU on GitHub-hosted runners to verify that all Python wheels and C-extensions (like `argon2-cffi` or `cryptography`) are available for ARM64 without being affected by local networking issues on self-hosted infrastructure. **Does not push to registry.**

### 3. Verify Functional (amd64)
*   **Runner:** `wsl-staging` (Self-hosted)
*   **Tasks:**
    *   Builds the `linux/amd64` image natively (no QEMU overhead).
    *   Starts the full stack (`nginx`, `web`, `mongo`, `redis`).
    *   **Smoke Test:** Explicitly verifies that the `web` container can reach the `nginx` proxy via the internal Docker network.
    *   **Pytest:** Runs the functional test suite (excluding e2e/performance).
    *   **Push:** If all tests pass, the verified image is pushed to `ghcr.io` for deployment.
*   **Rationale:** Functional verification happens on the self-hosted runner to mirror the production-like environment (WSL/Linux).

### 4. Deploy to WSL (Staging)
*   **Runner:** `wsl-staging` (Self-hosted)
*   **Trigger:** Only runs if *both* `Check ARM64 Wheels` and `Verify Functional (amd64)` succeed.
*   **Tasks:** Executes `scripts/deploy.sh` to update the staging environment with the newly verified image.

## Staging Deployment (WSL Runner)
**Triggered by:** Runs after the `build-and-test` job successfully completes.
**Runs on:** A self-hosted runner explicitly labeled `wsl-staging`.

**Key Steps:**
1.  **Checkout Code:** Retrieves the repository content.
2.  **Make Deploy Script Executable:** Ensures `scripts/deploy.sh` can be run.
3.  **Validate Required Secrets:** Checks for the presence of necessary secrets.
4.  **Deploy to WSL:** Executes `scripts/deploy.sh` which:
    *   Generates self-signed certificates.
    *   Optionally performs a hard reset (`down -v`) when manually triggered with `workflow_dispatch` input `hard_rebuild=true`; before reset it attempts a MongoDB backup archive.
    *   Auto-recovers once from Mongo auth/volume drift on staging (`DEPLOY_AUTO_RECOVER_MONGO_AUTH=true`) by performing a guarded hard reset if Mongo healthcheck reports `Authentication failed`.
    *   Executes `docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --wait --pull always --no-build`. This pulls the exact commit image from `ghcr.io` (via `docker-compose.ci.yml`) and starts all services.
    *   Waits for MongoDB service to be healthy and verifies authenticated MongoDB ping.
5.  **Verify Staging Health:** Runs `curl -f` check against `http://localhost:5000/` to ensure the application stack is responsive.
6.  **Create Admin & Seed DB:** Sets up the admin user and populates initial data (articles + profile) in the staging environment.

## Docker & Application Configuration
*   **Image Source:** `web` service in `docker-compose.yml` is `build: .` (for local dev). For CI/Staging, `docker-compose.ci.yml` overrides this to `image: ${IMAGE_TAG}` and disables build (pulled from `ghcr.io`). `mongo` and `redis` use their respective official Docker Hub images.
*   **Configurable Gunicorn Workers:** The `web` service's `Dockerfile` uses `${GUNICORN_WORKERS}` to set the number of Gunicorn worker processes. `docker-compose.yml` provides a safe default (e.g., `3`) via `GUNICORN_WORKERS: ${GUNICORN_WORKERS:-3}`.
*   **Gunicorn Hardening:** Gunicorn is configured with `--limit-request-line 4094`, `--limit-request-fields 100`, and `--max-requests 1000`. `--preload` is enabled to force atomic app factory loading, ensuring the container fails immediately if the application cannot bootstrap. `FORWARDED_ALLOW_IPS` is used to restrict which IPs the WSGI server trusts for proxy headers.
*   **Flask App Env:** `FLASK_ENV` is set to `development` for CI/test and `production` for staging/deployment.
*   **Talisman/HTTPS:** `TALISMAN_FORCE_HTTPS` is configured (default `true` for deployment).
*   **ProxyFix:** `PROXY_FIX_X_FOR`, `PROXY_FIX_X_PROTO`, etc., are configured to handle reverse proxy headers.
*   **Service Health Checks:** `mongo`, `redis`, and the `web` (Flask) services all have `healthcheck` definitions in `docker-compose.yml`. MongoDB healthcheck uses authenticated root credentials.
*   **MongoDB Auth Mode:** `web` connects via authenticated `MONGO_URI` using the app user. Mongo init script provisions app-user roles for both `appdb` and `pytest_appdb`.
*   **Mongo Start Grace:** Mongo healthcheck includes a start period to avoid false unhealthy status during first-time user/init script setup.

## Required GitHub Secrets
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `MONGO_ROOT_USER`
- `MONGO_ROOT_PASSWORD`
- `MONGO_APP_USER`
- `MONGO_APP_PASSWORD`

## Production Deployment (Raspberry Pi & Cloudflare)

The production environment leverages **Cloudflare Tunnels (Zero Trust)** for secure edge routing and identity-aware access.

### **1. Cloudflare Tunnels (The "Outbound-Only" Bridge)**
Instead of opening inbound ports (80/443) on your home router or server, the `cloudflared` container creates an **outbound-only** persistent connection to the Cloudflare Edge.
- **Security Benefit:** Your server's public IP remains hidden. There is no "attack surface" for port-scanners or traditional DDoS attacks because the server is not listening for connections from the internet.
- **Connectivity:** The tunnel acts as a virtual bridge, allowing Cloudflare to route traffic from your domain name directly to the Nginx container inside the Docker network.

### **2. Cloudflare Registered Domain & Edge TLS**
By using a domain registered with or managed by Cloudflare, you gain several "Edge" capabilities:
- **Automatic TLS Termination:** Cloudflare provides and automatically renews a globally trusted SSL/TLS certificate for your domain. Traffic from the user's browser to the Cloudflare Edge is encrypted using this certificate.
- **Internal Encryption ("Full" SSL Mode):** Traffic from the Cloudflare Edge through the tunnel to your Nginx container is encrypted using the project's **self-signed certificates** (generated during deployment). This ensures end-to-end encryption even within your local network.
- **Caching & Optimization:** Static assets (JS/CSS) are cached at Cloudflare's edge locations, reducing latency and offloading traffic from your Raspberry Pi.

### **3. Zero Trust Access (Identity-Aware Gate)**
Cloudflare Tunnels allow you to wrap the entire application in **Access Policies** before a single packet reaches your server:
- **Email OTP / 2FA:** You can configure a policy that requires users to authenticate via Email OTP or a supported SSO provider (GitHub, Google, etc.) at the Cloudflare Edge.
- **Authorization Matrix:** This acts as the first "gate" in our multi-layered security model. If a user is not authorized by Cloudflare, their request is blocked at the edge, protecting the application from unauthorized probes and recursive 401 hammering.

### **Production Service Stack**
In production, use the base and production override files:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Required Production Secrets**
In addition to the base secrets, production requires:
- `CLOUDFLARE_TUNNEL_TOKEN`: The unique token generated in the Cloudflare Zero Trust dashboard.
- `DOMAIN_NAME`: Your public domain (e.g., `spencerchristopher.com`).

### **Nginx Production Hardening**
Nginx is configured to trust Cloudflare headers:
- `CF-Connecting-IP`: Used to identify the true client IP for audit logging and rate limiting.
- `X-Forwarded-For`: Preserved through the tunnel to maintain request context.

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
*   Compose service names are `web`, `nginx`, `mongo`, and `redis`. For ad-hoc troubleshooting, use these with `docker compose ... logs`; container names (`flask_web_app`, `nginx_proxy`, `mongodb`) are for `docker logs`.

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
