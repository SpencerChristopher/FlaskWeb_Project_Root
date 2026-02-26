#!/bin/bash
set -e

CONTAINER_NAME="${CONTAINER_NAME:-flask_web_app}"

docker exec "$CONTAINER_NAME" /bin/sh -c "mkdir -p /app/tests"
docker cp tests/. "$CONTAINER_NAME":/app/tests
docker cp pytest.ini "$CONTAINER_NAME":/app/pytest.ini

# Determine if we should skip heavy tests (default to skip in CI for Pi optimization)
PYTEST_ARGS="/app/tests"
if [ "${OPT_IN_HEAVY_TESTS:-false}" != "true" ]; then
    echo "Running 'lite' test suite (excluding heavy tests)..."
    PYTEST_ARGS="-m 'not heavy' /app/tests"
else
    echo "Running 'full' test suite (including heavy tests)..."
fi

docker exec -e PYTHONPATH=/app "$CONTAINER_NAME" /app/.venv/bin/pytest $PYTEST_ARGS
