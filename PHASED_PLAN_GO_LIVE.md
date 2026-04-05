# Phased Plan: Go-Live Readiness & "Teething" Resolution

This plan outlines the sequential steps required to move the project from "Staging/WSL" to "Production/Raspberry Pi" with full stability, data integrity, and compliance.

---

## Task 1: Operational Stability (Log Rotation & Disk Safety) [DONE]
*Goal: Prevent the Raspberry Pi SD card from filling up and crashing MongoDB.*

### Stage 1: Docker Log Caps [DONE]
*   Updated `docker-compose.prod.yml` and `docker-compose.staging.yml` with global `logging` limits (3x10MB).

### Stage 2: Pruning Policy [DONE]
*   Added optional `docker image prune -af` to `scripts/deploy.sh`.

**Gate:** Verified `LogConfig` settings in compose files.

---

## Task 2: Frontend Resiliency ("Double-Gate" UX) [DONE]
*Goal: Gracefully handle session invalidation when `token_version` increments.*

### Stage 1: Global Fetch Interceptor [DONE]
*   Modified `static/app.js` to catch `401 Unauthorized` and redirect to `/login?reason=session_expired`.

### Stage 2: Security Feedback [DONE]
*   Updated `LoginView.js` to display security messages based on the `reason` query parameter.

**Gate:** Verified 401 redirect logic in SPA code.

---

## Task 3: Regulatory Compliance (GDPR Transparency) [DONE]
*Goal: Meet European transparency requirements for PII handling.*

### Stage 1: Privacy Policy View [DONE]
*   Implemented `/api/privacy` route and `PrivacyView.js`.

### Stage 2: Static Link Integration [DONE]
*   Added Privacy Policy link to `templates/base.html` footer.

**Gate:** Verified the `/privacy` page is accessible and correctly lists Cloudflare as a sub-processor.

---

## Task 4: Persistence & USB Backup Strategy [DONE]
*Goal: Shift high-write database operations to external storage and ensure "Hard Rebuild" safety.*

### Stage 1: Runner Scaffolding (Bootstrap Integration) [DONE]
*   Created `scripts/preflight_pi.sh` to verify USB mount (`/mnt/usb-storage`), Docker permissions, and NTP sync.
*   **Verified on Hardware:** Manually confirmed `/mnt/usb-storage/docker-volumes` and `/backups` are writable by `webapp` user.

### Stage 2: Deployment Script Guard [DONE]
*   Modified `scripts/deploy.sh` to prioritize `mongodump` to the USB backup directory.

**Gate:** Verified logic in `preflight_pi.sh` and `deploy.sh` on physical Pi 4.

---

## Task 5: Final Stress Verification [TODO]
*Goal: Confirm ARM64 performance parity.*

### Stage 1: Remote Benchmarking
*   Run `scripts/stress_test.py` against the **Live Raspberry Pi URL**.
*   Monitor memory usage on the Pi via `htop` during the test to ensure the 2GB limit isn't breached by Gunicorn workers.

**Gate:** Achieve >100 RPS with <500ms p95 latency on the physical hardware.
