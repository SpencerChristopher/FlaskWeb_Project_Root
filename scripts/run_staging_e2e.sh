#!/usr/bin/env bash
set -euo pipefail

REQUIRED_SECRETS=(
  SECRET_KEY
  ADMIN_USERNAME
  ADMIN_PASSWORD
  MONGO_ROOT_USER
  MONGO_ROOT_PASSWORD
  MONGO_APP_USER
  MONGO_APP_PASSWORD
  STAGING_TOKEN
  CF_ACCESS_JWT
)

for secret in "${REQUIRED_SECRETS[@]}"; do
  : "${!secret:?Environment variable $secret must be exported before running this script.}"
done

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.staging.yml"
E2E_BASE_URL=${E2E_BASE_URL:-https://staging.spencerscooking.uk}

docker compose ${COMPOSE_FILES} --env-file config.env up -d

# Install system dependencies (chromium requires root to install packages)
docker compose ${COMPOSE_FILES} --env-file config.env exec --user root web /app/.venv/bin/python -m playwright install-deps chromium
docker compose ${COMPOSE_FILES} --env-file config.env exec --user root web /app/.venv/bin/python -m playwright install chromium

# Run the E2E suite
docker compose ${COMPOSE_FILES} --env-file config.env exec web /app/.venv/bin/pytest /app/tests -m e2e --base-url="${E2E_BASE_URL}"
