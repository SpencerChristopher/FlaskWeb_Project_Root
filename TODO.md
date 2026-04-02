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

10. [DONE] GDPR & Data Sovereignty:
   - [DONE] Implement "Right to Erasure" (Delete Account) with re-authentication.
   - [DONE] Implement "Privacy by Design" (Bcrypt, Token Revocation).
   - [DONE] Implement cascaded cleanup (Comments deleted on User/Article removal).
   - [DONE] Add a public-facing "Privacy Policy" page explaining data usage.
   - [TODO] Implement "Right to Portability" (Export user data to JSON).
   - [TODO] Enable host-level encryption (LUKS/BitLocker) as documented in review.
11. [DONE] Raspberry Pi Storage & Backups:
   - Context: Pi 4 uses 64GB SD for OS/containers.
   - Goal: Add automated MongoDB backups to attached 32GB USB storage volume.
   - [DONE] Define backup retention + rotation logic in deployment scripts.
   - [DONE] Ensure backups run before any destructive reset and on a schedule.
   - [TODO] Document restore procedure and verify backups are readable.

12. Security & Identity Hardening:
   - [DONE] Cloudflare Zero Trust (Access): Easiest 2FA/Identity solution. Enforce email OTP/Social IdP at the edge to protect `/api/auth/login` and management routes.
   - [TODO] Native TOTP (Google Authenticator): Add as "Defense in Depth" backup to Zero Trust.
     - Note: Requires NTP (Network Time Protocol) on Raspberry Pi to prevent clock drift issues.
     - Strategy: Implement using `pyotp` with a ±1 verification window.

13. Review Architectural Patterns for Multi-User Transition:
   - Current state: Single-admin content model where the Admin is the only provider.
   - Requirement: Future migration to "True User Access" (Comments, User-Generated Content).
   - Task: Review Backend Singletons and Frontend Factory/Observer patterns to ensure they scale for multiple resource owners.
   - Task: Solidify the "Comment Service" and "Resource Ownership" patterns before expanding the user base.
