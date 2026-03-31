## TODO

1. [DONE] Make request timeouts configurable in CI/prod (Nginx, Gunicorn, Mongo).
2. [DONE] Remove deploy-key usage for self-hosted runner (Verified workflows).
3. [DONE] Add prod-only smoke tests (tests/smoke/test_prod_readiness.py).
4. [DONE] Bootstrapping script for Raspberry Pi (Managed in external repository).
5. [DEFERRED] Production workflow runtime fixes (Apply when prod env is live).
6. [DONE] Integrate Cloudflare Tunnel (docker-compose.prod.yml).
7. [DONE] Define TLS/cert mode for Cloudflare Tunnel (Nginx CF headers).
8. Optimize Test Suite for CI/Pi:
   - Evaluate moving high-payload integration tests (Profile API, Media) to a post-deploy smoke suite.
   - Keep core CI lightweight to reduce log bloat and save resources on Raspberry Pi.
9. [DONE] Enforce Resource Parity (Staging/Prod):
   - Goal: Make staging behave like Raspberry Pi prod (2GB RAM, ARM64 constraints) without destabilizing data.
   - [DONE] Add hard memory limits per service (web/mongo/redis/nginx) in staging/prod compose files.
   - [DONE] Prefer real enforcement (`mem_limit`/`cpus`) over `deploy.resources` (non‑Swarm).
   - [DONE] Define target budgets per service and document them (docs/DEPLOYMENT.md).
   - [DONE] Validate limits locally (WSL) and on staging; watch for OOM/restart loops.
   - Disk: document data growth expectations, ensure volumes persist, and avoid teardown unless explicitly triggered.
10. Raspberry Pi Storage & Backups:
   - Context: Pi 4 uses 64GB SD for OS/containers.
   - Goal: Add automated MongoDB backups to attached 32GB USB storage volume.
   - Define backup retention + rotation (e.g., daily + keep last N).
   - Ensure backups run before any destructive reset (hard_rebuild) and on a schedule.
   - Document restore procedure and verify backups are readable.
11. Review Architectural Patterns for Multi-User Transition:
   - Current state: Single-admin content model where the Admin is the only provider.
   - Requirement: Future migration to "True User Access" (Comments, User-Generated Content).
   - Task: Review Backend Singletons and Frontend Factory/Observer patterns to ensure they scale for multiple resource owners.
   - Task: Solidify the "Comment Service" and "Resource Ownership" patterns before expanding the user base.
