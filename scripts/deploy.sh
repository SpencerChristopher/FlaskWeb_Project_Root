#!/bin/bash
set -e

# Ensure image tag is provided by CI/CD
if [ -z "${IMAGE_TAG:-}" ]; then
  echo "IMAGE_TAG is not set."
  exit 1
fi

# The environment variables are passed directly from GitHub Actions;
# no need to create a .env file. This improves security by not writing secrets to disk.

echo "Ensuring certs directory..."
mkdir -p certs
if [ ! -f certs/server.key ] || [ ! -f certs/server.crt ]; then
  openssl genrsa -out certs/server.key 2048
  openssl req -x509 -sha256 -nodes -days 365 -new -key certs/server.key -out certs/server.crt -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
  chmod 600 certs/server.key
  chmod 644 certs/server.crt
fi

echo "Starting Docker Compose services with override..."
# docker-compose will automatically pick up docker-compose.override.yml
# provided it's in the same directory.
# We explicitly set RUN_MODE=https for the web service.
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --wait --pull always --no-build

echo "Waiting for MongoDB to be healthy..."
for i in {1..30}; do
  status=$(docker inspect -f '{{.State.Health.Status}}' mongodb 2>/dev/null || echo "unknown")
  if [ "$status" = "healthy" ]; then
    echo "MongoDB is healthy."
    break
  fi
  sleep 2
done

if [ "$status" != "healthy" ]; then
  echo "MongoDB did not become healthy in time."
  docker compose ps
  exit 1
fi

echo "Deployment complete."
