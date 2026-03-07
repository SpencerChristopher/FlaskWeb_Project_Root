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
9. Review Architectural Patterns for Multi-User Transition:
   - Current state: Single-admin content model where the Admin is the only provider.
   - Requirement: Future migration to "True User Access" (Comments, User-Generated Content).
   - Task: Review Backend Singletons and Frontend Factory/Observer patterns to ensure they scale for multiple resource owners.
   - Task: Solidify the "Comment Service" and "Resource Ownership" patterns before expanding the user base.
