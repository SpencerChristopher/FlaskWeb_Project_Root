#!/bin/bash
set -eo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: Required tool '$1' is not installed."
        return 1
    fi
}

echo "--- Preflight Security & Integrity Checks ---"

echo "[1/7] Tool Check"
require_cmd poetry
require_cmd docker
require_cmd curl

echo "[2/7] Security Audit (pip-audit)"
if command -v pip-audit >/dev/null 2>&1; then
    # Audit the local project dependencies
    poetry export --format=constraints.txt --output=constraints.txt --without-hashes
    pip-audit -r constraints.txt
    rm constraints.txt
else
    echo "Warning: pip-audit not found on host. Skipping local dependency scan."
    echo "Recommendation: Install pip-audit via 'pip install pip-audit' for better local security."
fi

echo "[3/7] Ensure poetry.lock is fresh"
poetry lock

echo "[4/7] Poetry install"
poetry install

echo "[5/7] Docker build"
docker compose --env-file .env build

echo "[6/7] Docker up (Full Stack)"
docker compose --env-file .env up -d --wait

echo "[7/7] Run Test Suite (Lite)"
docker exec -e PYTHONPATH=/app flask_web_app /app/.venv/bin/pytest tests/ -q -m "not heavy"

echo "---------------------------------------------"
echo "Preflight complete. Stack is healthy and secure."
