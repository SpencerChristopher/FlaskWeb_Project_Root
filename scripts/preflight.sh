#!/bin/bash
set -e

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "[1/6] Poetry lock (if needed)"
poetry lock

echo "[2/6] Poetry install"
poetry install

echo "[3/6] Docker build"
docker compose --env-file .env build

echo "[4/6] Docker up"
docker compose --env-file .env up -d

echo "[5/6] Run tests"
docker exec -e PYTHONPATH=/app flask_web_app /app/.venv/bin/pytest tests/ -q

echo "[6/6] HTTPS health check"
curl -k -I https://localhost/ | head -n 1

echo "Preflight complete."
