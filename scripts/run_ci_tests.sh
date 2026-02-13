#!/bin/bash
set -e

CONTAINER_NAME="${CONTAINER_NAME:-flask_web_app}"

docker exec "$CONTAINER_NAME" /bin/sh -c "mkdir -p /app/tests"
docker cp tests/. "$CONTAINER_NAME":/app/tests
docker cp pytest.ini "$CONTAINER_NAME":/app/pytest.ini
docker exec -e PYTHONPATH=/app "$CONTAINER_NAME" /app/.venv/bin/pytest /app/tests
