#!/bin/bash
set -e

# The environment variables are passed directly from GitHub Actions;
# no need to create a .env file. This improves security by not writing secrets to disk.

echo "Creating docker-compose.override.yml from template..."
cp docker-compose.override.yml.template docker-compose.override.yml

echo "Starting Docker Compose services with override..."
# docker-compose will automatically pick up docker-compose.override.yml
# provided it's in the same directory.
# We explicitly set RUN_MODE=https for the web service.
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build

echo "Deployment complete."