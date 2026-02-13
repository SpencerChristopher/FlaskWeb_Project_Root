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
