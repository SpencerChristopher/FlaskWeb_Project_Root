#!/bin/bash
set -euo pipefail

COMPOSE_ARGS=(-f docker-compose.yml -f docker-compose.ci.yml)

backup_before_reset() {
  if ! docker ps --format '{{.Names}}' | grep -q '^mongodb$'; then
    echo "MongoDB container not running; skipping pre-reset backup."
    return 0
  fi

  mkdir -p backups
  backup_path="backups/mongo-pre-reset-$(date +%Y%m%d-%H%M%S).archive.gz"
  echo "Creating MongoDB backup at ${backup_path}..."
  if docker exec mongodb sh -lc 'mongodump --archive --gzip --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin' > "${backup_path}"; then
    echo "MongoDB backup completed."
  else
    echo "MongoDB backup failed."
    if [ "${DEPLOY_REQUIRE_BACKUP:-true}" = "true" ]; then
      echo "Backup is required before volume reset. Aborting deployment."
      return 1
    fi
    echo "Continuing without backup because DEPLOY_REQUIRE_BACKUP is false."
  fi
}

# Ensure image tag is provided by CI/CD
if [ -z "${IMAGE_TAG:-}" ]; then
  echo "IMAGE_TAG is not set."
  exit 1
fi

echo "Ensuring certs directory..."
mkdir -p certs
if [ ! -f certs/server.key ] || [ ! -f certs/server.crt ]; then
  openssl genrsa -out certs/server.key 2048
  openssl req -x509 -sha256 -nodes -days 365 -new -key certs/server.key -out certs/server.crt -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
  chmod 600 certs/server.key
  chmod 644 certs/server.crt
fi

if [ "${DEPLOY_CLEAN_START:-false}" = "true" ]; then
  if [ "${DEPLOY_RESET_VOLUMES:-false}" = "true" ]; then
    echo "Performing hard reset with volume removal..."
    if [ "${DEPLOY_BACKUP_BEFORE_RESET:-true}" = "true" ]; then
      backup_before_reset
    fi
    docker compose "${COMPOSE_ARGS[@]}" down -v --remove-orphans || true
  else
    echo "Performing clean compose start..."
    docker compose "${COMPOSE_ARGS[@]}" down --remove-orphans || true
  fi
fi

echo "Starting Docker Compose services with override..."
docker compose "${COMPOSE_ARGS[@]}" up -d --wait --pull always --no-build --remove-orphans

echo "Waiting for MongoDB to be healthy..."
status="unknown"
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
  docker compose "${COMPOSE_ARGS[@]}" ps
  exit 1
fi

echo "Verifying authenticated MongoDB connectivity..."
if ! docker exec mongodb sh -lc 'mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand(\"ping\").ok"' | grep -q "1"; then
  echo "Authenticated MongoDB ping failed."
  exit 1
fi

echo "Deployment complete."
