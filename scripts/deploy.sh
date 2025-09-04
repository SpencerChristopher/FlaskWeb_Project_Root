#!/bin/bash
set -e

# Check for required environment variables
if [ -z "$SECRET_KEY" ]; then
  echo "Error: SECRET_KEY environment variable is not set."
  exit 1
fi

if [ -z "$LOG_LEVEL" ]; then
  echo "Error: LOG_LEVEL environment variable is not set."
  exit 1
fi

echo "Starting Docker Compose services..."

# Export the variables so docker-compose can access them
export SECRET_KEY
export LOG_LEVEL

docker compose up -d --build

echo "Deployment complete."