#!/bin/bash
set -e

echo "Starting Docker Compose services..."
docker compose up -d --build

echo "Deployment complete."
