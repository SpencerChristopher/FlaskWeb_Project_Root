#!/bin/bash
set -e

# The environment variables are passed directly from GitHub Actions;
# no need to create a .env file. This improves security by not writing secrets to disk.

echo "Creating docker-compose.override.yml from template..."
cp docker-compose.override.yml.template docker-compose.override.yml

echo "Setting default non-secret config for deployment..."
: "${JWT_COOKIE_SECURE:=true}"
: "${JWT_COOKIE_CSRF_PROTECT:=true}"
: "${JWT_COOKIE_SAMESITE:=Lax}"
: "${PROXY_FIX_X_FOR:=1}"
: "${PROXY_FIX_X_PROTO:=1}"
: "${PROXY_FIX_X_HOST:=1}"
: "${PROXY_FIX_X_PREFIX:=1}"
: "${CORS_ORIGINS:=https://localhost,https://127.0.0.1}"

echo "Starting Docker Compose services with override..."
# docker-compose will automatically pick up docker-compose.override.yml
# provided it's in the same directory.
# We explicitly set RUN_MODE=https for the web service.
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build

echo "Deployment complete."
