## TODO

1. Make request timeouts configurable in CI/prod:
   - Nginx `proxy_read_timeout`, `proxy_send_timeout`, `proxy_connect_timeout`
   - Gunicorn `--timeout`
   - Align Mongo driver timeouts with app/proxy budgets
2. Remove deploy-key usage for self-hosted runner:
   - Drop `ssh-key` from `actions/checkout` in `.github/workflows/test-deploy.yml`
   - Remove repo deploy key and related `SSH_PRIVATE_KEY_*` secrets if runner is already registered
3. Add prod-only smoke tests:
   - Run minimal health checks (startup, DB connectivity, auth) in prod once env is ready
   - Keep full suite in CI/staging to avoid prod side-effects
4. Create a new bootstrapping script for Raspberry Pi:
   - Adapt `runner_bootstrap.sh` to dynamically detect ARM architecture.
   - Adjust `wsl_bootstrap.sh` (minor changes) for non-WSL environment.
   - Ensure it creates a robust environment for the production GitHub Actions runner.
5. Defer production workflow runtime fixes (apply when prod env is live):
   - Update `.github/workflows/production-deploy.yml` to use `/app/.venv/bin/python` for admin/seed scripts.
   - Align prod deploy steps with staging compose flags (`--remove-orphans`, explicit compose files).
6. Integrate Cloudflare Tunnel for production edge routing:
   - Add a `cloudflared` endpoint container (prod compose override) and wire it to the app/nginx service.
   - Store tunnel credentials/token in GitHub Actions secrets and inject only in prod jobs.
   - Add smoke checks for tunnel reachability and upstream app health.
7. Define TLS/cert mode when Cloudflare Tunnel is enabled:
   - Keep self-signed certs for local/Wsl fallback only.
   - Document tunnel mode where Cloudflare handles TLS termination, and internal traffic uses private network paths.
   - Ensure app/proxy settings (`TALISMAN_FORCE_HTTPS`, forwarded headers) match tunnel behavior.
8. Optimize Test Suite for CI/Pi:
   - Evaluate moving high-payload integration tests (Profile API, Media) to a post-deploy smoke suite.
   - Keep core CI lightweight to reduce log bloat and save resources on Raspberry Pi.
