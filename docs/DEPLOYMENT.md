# Deployment & CI/CD

This document covers deployment flow, CI/CD, runner expectations, and environment configuration.

## Overview
- CI runs on GitHub Actions (build + test).
- Deploy runs on the WSL runner using `scripts/deploy.sh`.
- Nginx terminates TLS and proxies to the Flask API.

## Environment Configuration
**Source of defaults**
- `config.env` contains non-secret defaults (committed).
- `.env` contains local overrides and secrets (not committed).
- Secrets for CI/CD are injected via GitHub Secrets.

**Key production flags**
- `FLASK_ENV=production`
- `TALISMAN_FORCE_HTTPS=true`

## CI Pipeline (dev branch)
Steps in `.github/workflows/test-deploy.yml`:
1. Checkout, install dependencies.
2. Generate self-signed certs (CI only).
3. Build images and run containers.
4. Seed DB, run tests.
5. Tear down containers.

## WSL Deploy
Triggered after successful build/test:
1. Checkout on runner.
2. Generate or reuse certs.
3. Run `scripts/deploy.sh`.
4. Optionally seed DB and create admin.

## Certificates
Nginx expects:
- `./certs/server.crt`
- `./certs/server.key`

CI/WSL uses self-signed certs. Production certs (e.g. Cloudflare) can replace these later without changing paths.

## Runners & Permissions
- WSL runner must have Docker access.
- Deployment avoids `sudo` by using container-based ownership fixes where needed.

## Notes
- Keep Mongo/Redis ports internal unless you explicitly enable exposure for local debugging.
- Use `config.env` as the shared baseline; override only what you must in CI/WSL.
