#!/bin/bash
set -euo pipefail

COMPOSE_ARGS=(-f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.staging.yml)

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

backup_before_reset_optional() {
  if [ "${DEPLOY_BACKUP_BEFORE_RESET:-true}" = "true" ]; then
    DEPLOY_REQUIRE_BACKUP="false" backup_before_reset || true
  fi
}

start_compose_stack() {
  docker compose "${COMPOSE_ARGS[@]}" up -d --wait --pull always --no-build --remove-orphans
}

mongo_is_auth_unhealthy() {
  local status
  status=$(docker inspect -f '{{.State.Health.Status}}' mongodb 2>/dev/null || echo "unknown")
  if [ "$status" != "unhealthy" ]; then
    return 1
  fi

  docker inspect --format '{{range .State.Health.Log}}{{println .Output}}{{end}}' mongodb 2>/dev/null | grep -qi "Authentication failed"
}

wait_for_mongo_healthy() {
  local status="unknown"
  for i in {1..30}; do
    status=$(docker inspect -f '{{.State.Health.Status}}' mongodb 2>/dev/null || echo "unknown")
    if [ "$status" = "healthy" ]; then
      echo "MongoDB is healthy."
      return 0
    fi
    sleep 2
  done

  echo "MongoDB did not become healthy in time."
  docker compose "${COMPOSE_ARGS[@]}" ps || true
  return 1
}

verify_mongo_auth_ping() {
  docker exec mongodb sh -lc 'mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand(\"ping\").ok"' | grep -q "1"
}

perform_mongo_auth_recovery() {
  echo "Detected MongoDB auth health drift. Aborting destructive auto-recovery."
  echo "Manual intervention required. Check volume permissions or auth credentials."
  return 1
}

# Ensure image tag is provided by CI/CD
if [ -z "${IMAGE_TAG:-}" ]; then
  echo "IMAGE_TAG is not set."
  exit 1
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
did_auto_recovery="false"
if ! start_compose_stack; then
  if [ "${DEPLOY_AUTO_RECOVER_MONGO_AUTH:-false}" = "true" ] && mongo_is_auth_unhealthy; then
    did_auto_recovery="true"
    perform_mongo_auth_recovery
  else
    echo "Compose startup failed."
    docker compose "${COMPOSE_ARGS[@]}" ps || true
    exit 1
  fi
fi

echo "Waiting for MongoDB to be healthy..."
if ! wait_for_mongo_healthy; then
  if [ "${DEPLOY_AUTO_RECOVER_MONGO_AUTH:-false}" = "true" ] && [ "$did_auto_recovery" = "false" ] && mongo_is_auth_unhealthy; then
    did_auto_recovery="true"
    perform_mongo_auth_recovery
    wait_for_mongo_healthy
  else
    exit 1
  fi
fi

echo "Verifying authenticated MongoDB connectivity..."
if ! verify_mongo_auth_ping; then
  if [ "${DEPLOY_AUTO_RECOVER_MONGO_AUTH:-false}" = "true" ] && [ "$did_auto_recovery" = "false" ] && mongo_is_auth_unhealthy; then
    did_auto_recovery="true"
    perform_mongo_auth_recovery
    wait_for_mongo_healthy
    verify_mongo_auth_ping
  else
    echo "Authenticated MongoDB ping failed."
    exit 1
  fi
fi

echo "Deployment complete."
